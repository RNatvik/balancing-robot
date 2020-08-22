import serial_package as sp
import proccom
import time
import json


class ArduinoLink:

    def __init__(self, tcp_host: str, tcp_port: int, com_port: str, baudrate: int, register_map: dict):
        """
        Create an ArduinoLink instance

        :param tcp_host: the host ip of the proccom server
        :param tcp_port: the host port of the proccom server
        :param com_port: the serial port of the arduino / serial device
        :param baudrate: the baud rate of the serial device
        :param register_map: a dictionary for mapping register numbers to type and name with
         keys "type", "number_to_name" and "name_to_number"
        """
        self.register_map = register_map
        self.protocol = sp.RACProtocol(register_map['type'], input_pad=True)
        self.protocol_executor = sp.ProtocolExecutor(self.protocol, self._input_handler, com_port, baudrate, debug=True)
        self.publisher = proccom.Publisher(
            'arduino_output', 'arduino_link_pub', self._format_data, host=tcp_host, port=tcp_port
        )
        self.subscriber = proccom.Subscriber(
            {'arduino_cmd': self._arduino_cmd_callback, 'shutdown_cmd': self._shutdown_msg_handler}, 'arduino_link_sub',
            host=tcp_host, port=tcp_port
        )

    def start(self, delay=5, print_status=True):
        """
        Start node

        :param delay: delay time between establishing contact with arduino and connecting to proccom server
        :param print_status: Print messages regarding to establishing communication
        :return: None
        """
        executor_started = self.protocol_executor.start()
        if executor_started:
            if print_status:
                print(self, ':: Protocol executor establishing communication...')
            time.sleep(delay)
            if executor_started:
                if print_status:
                    print(self, ':: Protocol executor establishing communication...')
                if print_status:
                    print(self, ':: Connecting Proccom publisher and subscriber...')
                self.publisher.connect()
                self.subscriber.connect()
                if print_status:
                    print(self, ':: DONE')
        else:
            print(self, ':: Protocol executor encountered an exception and could not start.')

    def stop(self):
        """
        Stop all processes
        :return:
        """
        print(self, 'in stop')
        self.protocol_executor.stop()
        self.publisher.stop()
        self.subscriber.stop()

    def _input_handler(self, data):
        """
        Handle input from arduino

        :param data:
        :return:
        """
        self.publisher.publish(data)

    def _format_data(self, data):
        """
        Format data to publish on proccom server

        :param data: list of tuples from serial protocol [(register1, value1), (register2, value2), ...]
        :return: {'register_name1': value1, 'register_name2': value2, ...}
        """
        output = {}
        for register, value in data:
            reg_name = self.register_map['number_to_name'][register]
            output[reg_name] = value

        # The following code is only used for testing purposes. Remove when finished
        acc_registers = ['acc_x', 'acc_y', 'acc_z']
        gyro_registers = ['gyro_x', 'gyro_y', 'gyro_z']
        print('____________')
        for acc, gyro in zip(acc_registers, gyro_registers):
            output[acc] = output[acc] / 16384
            output[gyro] = output[gyro] / 131
            print(f'{acc}: {round(output[acc], 5)}    {gyro}: {round(output[gyro], 5)}')
        print('____________')
        # Test code end
        return output

    def _arduino_cmd_callback(self, msg):
        """
        Handle incoming messages from proccom server related to arduino commands
        msg['data'] should be formatted as: {'register_name1': value1, 'register_name2': value2, ... }

        :param msg: a proccom formatted message
        :return: None
        """
        data: dict = msg['data']
        registers = data.keys()
        a = []
        for reg_name in registers:
            reg_num = self.register_map['name_to_number'][reg_name]
            value = data[reg_name]
            a.append((reg_num, value))
        self.protocol_executor.set_data(a)

    def _shutdown_msg_handler(self, msg):
        """
        Handles messages related to shutting down the node from the proccom server

        :param msg: a proccom formatted message
        :return: None
        """
        data = msg['data']
        name = data['name']
        if name == self.subscriber.id:
            shutdown = data['value']
            if shutdown:
                self.stop()


def main(server_config_path, arduino_config_path):
    """
    Start the arduino_link node

    :param server_config_path: path to the json file describing server configuration
    :param arduino_config_path: path to the json file describing arduino configuration
    :return:
    """
    # Open relevant config files
    with open(server_config_path, 'r') as server_file:
        server_config = json.load(server_file)
    with open(arduino_config_path, 'r') as arduino_file:
        arduino_config = json.load(arduino_file)
    tcp_host = server_config['host']
    tcp_port = server_config['port']
    serial_port = arduino_config['com_port']
    baudrate = arduino_config['baudrate']
    registers = arduino_config['registers']
    type_map = arduino_config['type_map']

    # Create register mapping from config file
    register_map = {
        "type": {register['reg_num']: type_map[register['type']] for register in registers},
        "number_to_name": {register['reg_num']: register['name'] for register in registers},
        "name_to_number": {register['name']: register['reg_num'] for register in registers}
    }

    ard_link = ArduinoLink(tcp_host, tcp_port, serial_port, baudrate, register_map)
    ard_link.start()


if __name__ == '__main__':
    main("../config/server.json", "../config/arduino.json")
