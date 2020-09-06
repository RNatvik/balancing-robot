import os
import time
import proccom
import dsp
import json
import math


class FeedbackInterpreter:

    def __init__(self, tcp_host, tcp_port, acc_config, gyro_config, filter_config):
        self.publisher = proccom.Publisher('feedback', 'feedback_pub', self._format_msg, host=tcp_host, port=tcp_port)
        self.subscriber = proccom.Subscriber(
            {'arduino_output': self._handle_arduino, 'shutdown_cmd': self._handle_shutdown},
            'feedback_sub', host=tcp_host, port=tcp_port
        )
        self.acc_config = acc_config
        self.gyro_config = gyro_config
        acc_coefficients = filter_config['accelerometer_coefficients']
        gyro_coefficients = filter_config['gyro_coefficients']
        self.comp_alpha = filter_config['complementary_alpha']
        self.acc_filter = dsp.core.MultiChannelFilter(3, acc_coefficients['num'])
        self.gyro_filter = dsp.core.MultiChannelFilter(3, gyro_coefficients['num'])

        self.t0 = time.time()
        self.roll = 0
        self.pitch = 0
        self.yaw = 0

        self.test_t0 = time.time()
        self.test_roll = 0
        self.test_pitch = 0
        self.test_yaw = 0

    def start(self):
        self.publisher.connect()
        self.subscriber.connect()

    def stop(self):
        self.publisher.stop()
        self.subscriber.stop()

    def _handle_arduino(self, msg):
        data = msg['data']
        acc, gyro = self._extract_imu(data)
        acc_filtered = self.acc_filter.filter_values(acc)
        gyro_filtered = self.gyro_filter.filter_values(gyro)
        orientation = self._calculate_orientation(acc_filtered, gyro_filtered)

        # Function call to calculate raw elements. Useful for debugging and calibrating
        # Acc orientation, gyro orientation
        t_acc_roll, t_acc_pitch, t_gyro_roll, t_gyro_pitch, t_gyro_yaw = self._calculate_test_data(acc, gyro)

        actual_output = {'orientation': orientation, 'acc': acc_filtered, 'gyro': gyro_filtered}
        raw_output = {
            'acc': {
                'roll': t_acc_roll,
                'pitch': t_acc_pitch,
                'values': acc
            },
            'gyro': {
                'roll': t_gyro_roll,
                'pitch': t_gyro_pitch,
                'yaw': t_gyro_yaw,
                'values': gyro
            }
        }
        self.publisher.publish(actual_output, raw_output)

    def _extract_imu(self, data: dict):
        acc_raw = [data['acc_x'], data['acc_y'], data['acc_z']]
        gyro_raw = [data['gyro_x'], data['gyro_y'], data['gyro_z']]
        acc = [a / self.acc_config['scale'] - offset for a, offset in zip(acc_raw, self.acc_config['offset'])]
        gyro = [g / self.gyro_config['scale'] - offset for g, offset in zip(gyro_raw, self.gyro_config['offset'])]
        return acc, gyro

    def _calculate_orientation(self, acc, gyro):
        # TODO: Figure out what units are applied to acc_roll and gyro_roll
        t = time.time()
        dt = t - self.t0
        self.t0 = t
        acc_roll = math.atan2(acc[1], acc[2]) * 180 / math.pi
        acc_pitch = math.atan2(-acc[0], math.sqrt(acc[1] ** 2 + acc[2] ** 2)) * 180 / math.pi
        self.roll = self.comp_alpha * (self.roll + gyro[0] * dt) + (1 - self.comp_alpha) * acc_roll
        self.pitch = self.comp_alpha * (self.pitch + gyro[1] * dt) + (1 - self.comp_alpha) * acc_pitch
        self.yaw += gyro[2] * dt

        return self.roll, self.pitch, self.yaw

    def _calculate_test_data(self, acc, gyro):
        t = time.time()
        dt = t - self.test_t0
        self.test_t0 = t
        acc_roll = math.atan2(acc[1], acc[2])
        acc_pitch = math.atan2(-acc[0], math.sqrt(acc[1] ** 2 + acc[2] ** 2))
        self.test_roll += gyro[0] * dt
        self.test_pitch += gyro[1] * dt
        self.test_yaw += gyro[2] * dt

        return acc_roll, acc_pitch, self.test_roll, self.test_pitch, self.test_yaw

    def _handle_shutdown(self, msg):
        data = msg['data']
        name = data['name']
        if name == self.subscriber.id:
            shutdown = data['value']
            if shutdown:
                self.stop()

    def _format_msg(self, actual, raw):
        return {
            "output": actual,
            "raw": raw
        }


def main(server_config_path, imu_config_path):
    with open(server_config_path, 'r') as server_file:
        server_config = json.load(server_file)
    with open(imu_config_path, 'r') as imu_file:
        imu_config = json.load(imu_file)

    tcp_host = server_config['host']
    tcp_port = server_config['port']

    acc_config = imu_config['accelerometer']
    gyro_config = imu_config['gyro']
    filter_config = imu_config['filter']

    interpreter = FeedbackInterpreter(tcp_host, tcp_port, acc_config, gyro_config, filter_config)
    interpreter.start()


if __name__ == '__main__':
    path = os.path.dirname(os.path.abspath(__file__))
    os.chdir(path)
    main("../config/server.json", "../config/imu.json")
