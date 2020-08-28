import proccom
import json


class Regulator:

    def __init__(self, server_host, server_port, physical_param, regulator_param):
        self.publisher = proccom.Publisher(
            'arduino_cmd', 'regulator_pub', self.format_msg, host=server_host, port=server_port
        )
        self.subscriber = proccom.Subscriber(
            {'feedback': self.handle_feedback, 'reference': self.handle_reference},
            'regulator_sub', host=server_host, port=server_port
        )
        self.base_time = regulator_param['base_time']
        self.physical_param = physical_param

    def format_msg(self, data):
        pass

    def handle_feedback(self, msg):
        pass

    def handle_reference(self, msg):
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


if __name__ == '__main__':
    main('../config/server.json', '../config/regulator.json')
