import json
import time
import os
import proccom


class Calibrator:

    def __init__(self, topic: str, acc_config, gyro_config, host='127.0.0.1', port='5000'):
        self.subscriber = proccom.Subscriber({topic: self._handle_feedback}, 'calibrator', host=host, port=port)
        self.acc_config = acc_config
        self.gyro_config = gyro_config
        self.data = {
            "ax": [],
            "ay": [],
            "az": [],
            "gx": [],
            "gy": [],
            "gz": []
        }

    def start(self):
        self.subscriber.connect()

    def stop(self, output_file_path):
        self.subscriber.stop()
        acc_offset, gyro_offset = self._calibrate_values()
        with open(output_file_path, 'r') as file:
            output_data = json.load(file)
        output_data['accelerometer']['offset'] = acc_offset
        output_data['gyro']['offset'] = gyro_offset
        with open(output_file_path, 'w') as file:
            json.dump(output_data, file, indent=2)

    def _calibrate_values(self):
        gyro_target = [0, 0, 0]
        acc_target = [0, 0, -1]
        # Calculate averages. Add offset from config file to simulate raw values
        mean_ax = sum(self.data['ax'] + self.acc_config['offset']) / len(self.data['ax'])
        mean_ay = sum(self.data['ay'] + self.acc_config['offset']) / len(self.data['ay'])
        mean_az = sum(self.data['az'] + self.acc_config['offset']) / len(self.data['az'])
        mean_gx = sum(self.data['gx'] + self.gyro_config['offset']) / len(self.data['gx'])
        mean_gy = sum(self.data['gy'] + self.gyro_config['offset']) / len(self.data['gy'])
        mean_gz = sum(self.data['gz'] + self.gyro_config['offset']) / len(self.data['gz'])
        oax = mean_ax - acc_target[0]
        oay = mean_ay - acc_target[1]
        oaz = mean_az - acc_target[2]
        ogx = mean_gx - gyro_target[0]
        ogy = mean_gy - gyro_target[1]
        ogz = mean_gz - gyro_target[2]

        print(f'Samples: {len(self.data["ax"])}\n'
              f'Accelerometer:\n'
              f'    Mean:\n'
              f'        x: {mean_ax}\n'
              f'        y: {mean_ay}\n'
              f'        z: {mean_az}\n'
              f'    Offset:\n'
              f'        x: {oax}\n'
              f'        x: {oay}\n'
              f'        x: {oaz}\n'
              f'Gyroscope:\n'
              f'    Mean:\n'
              f'        x: {mean_gx}\n'
              f'        y: {mean_gy}\n'
              f'        z: {mean_gz}\n'
              f'    Offset:\n'
              f'        x: {ogx}\n'
              f'        x: {ogy}\n'
              f'        x: {ogz}\n'
              f'Target:\n'
              f'    Accelerometer: {acc_target}\n'
              f'    Gyroscope:     {gyro_target}')

        return [oax, oay, oaz], [ogx, ogy, ogz]

    def _handle_feedback(self, msg):
        data = msg['data']
        raw_acc = data['output']['acc']
        raw_gyro = data['output']['gyro']
        self.data['ax'].append(raw_acc[0])
        self.data['ay'].append(raw_acc[1])
        self.data['az'].append(raw_acc[2])
        self.data['gx'].append(raw_gyro[0])
        self.data['gy'].append(raw_gyro[1])
        self.data['gz'].append(raw_gyro[2])


def main(server_config_path, imu_config_path):
    path = os.path.dirname(os.path.abspath(__file__))
    os.chdir(path)
    with open(server_config_path, 'r') as server_file:
        server_config = json.load(server_file)
    with open(imu_config_path, 'r') as imu_file:
        imu_config = json.load(imu_file)
    host = server_config['host']
    port = server_config['port']
    acc_config = imu_config['accelerometer']
    gyro_config = imu_config['gyro']
    calibrator = Calibrator('feedback', acc_config, gyro_config, host=host, port=port)
    calibrator.start()
    time.sleep(30)
    calibrator.stop(imu_config_path)


if __name__ == '__main__':
    main('../config/server.json', '../config/imu.json')
