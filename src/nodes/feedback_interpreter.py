import proccom
import dsp
import json


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

        self.acc_filter = dsp.core.MultiChannelFilter(3, acc_coefficients['num'], a=acc_coefficients['den'])
        self.gyro_filter = dsp.core.MultiChannelFilter(3, gyro_coefficients['num'], a=gyro_coefficients['den'])

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

    def _extract_imu(self, data: dict):
        acc_raw = [data['acc_x'], data['acc_y'], data['acc_z']]
        gyro_raw = [data['gyro_x'], data['gyro_y'], data['gyro_z']]
        acc = [a/self.acc_config['scale'] - offset for a, offset in zip(acc_raw, self.acc_config['offset'])]
        gyro = [g/self.gyro_config['scale'] - offset for g, offset in zip(gyro_raw, self.gyro_config['offset'])]
        return acc, gyro

    def _calculate_orientation(self, acc, gyro):

        return self.gyro_filter

    def _handle_shutdown(self, msg):
        pass

    def _format_msg(self, data):
        pass


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


if __name__ == '__main__':
    main("../config/server.json", "../config/imu.json")