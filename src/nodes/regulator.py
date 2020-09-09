import os
import time

import proccom
import json
import math
from helpers.pid import PID


class Regulator:

    def __init__(self, server_host, server_port, physical_param, regulator_param):
        self.publisher = proccom.Publisher(
            'arduino_cmd', 'regulator_pub', self.format_msg, host=server_host, port=server_port
        )
        self.subscriber = proccom.Subscriber(
            {'feedback': self.handle_feedback, 'regulator_settings': self.handle_settings},
            'regulator_sub', host=server_host, port=server_port
        )
        self.pid = PID(
            regulator_param['p'], regulator_param['i'], regulator_param['d'],
            ilim=regulator_param['ilim'], olim=regulator_param['olim']
        )
        self.base_time = regulator_param['base_time']
        self.min_dd = regulator_param['min_dd']
        self.max_dd = regulator_param['max_dd']
        self.cutoff = regulator_param['cutoff_threshold']
        self.physical_param = physical_param
        self.reference = 0

        self.first_output = True
        self.prev_dd0 = self.max_dd
        self.prev_dd1 = self.max_dd
        self.prev_enable0 = False
        self.prev_enable1 = False
        self.prev_reverse0 = False
        self.prev_reverse1 = False

    def start(self):
        self.subscriber.connect()
        self.publisher.connect()
        time.sleep(1)
        self.publisher.publish(
            [self.prev_dd0, self.prev_dd1],
            [self.prev_reverse0, self.prev_reverse1],
            [self.prev_enable0, self.prev_enable1]
        )
        self.pid.initialize()

    def stop(self):
        self.subscriber.stop()
        self.publisher.stop()

    def format_msg(self, drive_delay, reverse, enable):
        drive_delay[0] = round(drive_delay[0])
        drive_delay[1] = round(drive_delay[1])
        if self.first_output:
            output = {
                "drive_delay1": drive_delay[0],
                "drive_delay2": drive_delay[1],
                "drive_enable1": enable[0],
                "drive_enable2": enable[1],
                "dir_state1": reverse[0],
                "dir_state2": not reverse[1]
            }
            self.first_output = False
        else:
            output = {}
            if self.prev_dd0 != drive_delay[0]:
                output['drive_delay1'] = drive_delay[0]
            if self.prev_dd1 != drive_delay[1]:
                output['drive_delay2'] = drive_delay[1]
            if self.prev_enable0 != enable[0]:
                output['drive_enable1'] = enable[0]
            if self.prev_enable1 != enable[1]:
                output['drive_enable2'] = enable[1]
            if self.prev_reverse0 != reverse[0]:
                output['dir_state1'] = reverse[0]
            if self.prev_reverse1 != reverse[1]:
                output['dir_state2'] = not reverse[1]
        self.prev_dd0 = drive_delay[0]
        self.prev_dd1 = drive_delay[1]
        self.prev_enable0 = enable[0]
        self.prev_enable1 = enable[1]
        self.prev_reverse0 = reverse[0]
        self.prev_reverse1 = reverse[1]
        return output

    def handle_feedback(self, msg):
        data = msg['data']
        output = data['output']
        # roll = output['orientation'][0]  # Currently redundant
        pitch = output['orientation'][1]
        # yaw = output['orientation'][2]  # Currently redundant
        reference = self.reference  # Copy internal variable for thread safety
        pid_out = self.pid.calculate(pitch, reference)  # rev/s
        if pid_out is not None:
            reverse = pid_out < 0
            w = abs(pid_out * 2 * math.pi)  # Convert pid_out to rad/s
            enable = w > self.cutoff
            if enable:
                dd = math.pi / (2 * w * self.base_time * 100)
            else:
                dd = self.max_dd
            self.publisher.publish([dd, dd], [reverse, reverse], [enable, enable])
            print(f'pid_out: {round(pid_out, 5)}, w: {round(w, 5)}, dd: {dd}')
        else:
            pass  # TODO: handle or ignore?

    def handle_settings(self, msg):
        pass


def main(server_config_path, regulator_config_path):
    with open(server_config_path, 'r') as server_file:
        server_config = json.load(server_file)
    with open(regulator_config_path, 'r') as regulator_file:
        regulator_config = json.load(regulator_file)
    server_host = server_config['host']
    server_port = server_config['port']
    physical_param = regulator_config['physical']
    regulator_param = regulator_config['params']

    regulator = Regulator(server_host, server_port, physical_param, regulator_param)
    regulator.start()
    time.sleep(60)
    regulator.stop()


if __name__ == '__main__':
    # path = os.path.dirname(os.path.abspath(__file__))
    # os.chdir(path)
    main('../config/server.json', '../config/regulator.json')
