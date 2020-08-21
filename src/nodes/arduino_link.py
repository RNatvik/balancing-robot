import serial_package as sp
import proccom
import time


class ArduinoLink:
    """
    TODO: Make an external file for arduino config (register_map, comport, baudrate, etc..)
    """

    def __init__(self, tcp_host: str, tcp_port: int, com_port: str, baudrate: int, register_map: dict):
        self.register_name_map = register_map['name']  # {'register_name': register_number}
        self.register_number_map = {self.register_name_map[key]: key for key in self.register_name_map.keys()}  # {register_number: 'register_name'}
        self.protocol = sp.RACProtocol(register_map['type'], input_pad=True)
        self.protocol_executor = sp.ProtocolExecutor(self.protocol, self._input_handler, com_port, baudrate)
        self.publisher = proccom.Publisher(
            'arduino_output', 'arduino_link_pub', self._format_data, host=tcp_host, port=tcp_port
        )
        self.subscriber = proccom.Subscriber(
            {'arduino_cmd': self._arduino_cmd_callback, 'shutdown_cmd': self._shutdown_msg_handler}, 'arduino_link_sub', host=tcp_host, port=tcp_port
        )

    def start(self, delay=5, print_status=True):
        self.protocol_executor.start()
        if print_status:
            print(self, ':: Protocol executor establishing communication...')
        time.sleep(delay)
        if print_status:
            print(self, ':: Connecting Proccom publisher and subscriber...')
        self.publisher.connect()
        self.subscriber.connect()
        if print_status:
            print(self, ':: DONE')

    def stop(self):
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
            reg_name = self.register_number_map[register]
            output[reg_name] = value
        return output

    def _arduino_cmd_callback(self, msg):
        """
        Handle incoming messages from proccom server
        msg['data'] should be formatted as: {'register_name1': value1, 'register_name2': value2, ... }
        :param msg:
        :return:
        """
        data: dict = msg['data']
        registers = data.keys()
        a = []
        for reg_name in registers:
            reg_num = self.register_name_map[reg_name]
            value = data[reg_name]
            a.append((reg_num, value))
        self.protocol_executor.set_data(a)

    def _shutdown_msg_handler(self, msg):
        data = msg['data']
        name = data['name']
        if name == self.subscriber.id:
            shutdown = data['value']
            if shutdown:
                self.stop()


def main():
    register_map = {
        'type': {
            0: sp.RACProtocol.INT,  # This register corresponds to drive_delay1
            1: sp.RACProtocol.INT,  # This register corresponds to drive_delay2
            2: sp.RACProtocol.BOOL,  # This register corresponds to drive_enable1
            3: sp.RACProtocol.BOOL,  # This register corresponds to drive_enable2
            4: sp.RACProtocol.ULONG,  # This register corresponds to step_counter1
            5: sp.RACProtocol.ULONG,  # This register corresponds to step_counter2
            6: sp.RACProtocol.UINT,  # This register corresponds to transmit_rate
            7: sp.RACProtocol.INT,  # This register corresponds to acc_x
            8: sp.RACProtocol.INT,  # This register corresponds to acc_y
            9: sp.RACProtocol.INT,  # This register corresponds to acc_z
            10: sp.RACProtocol.INT,  # This register corresponds to gyro_x
            11: sp.RACProtocol.INT,  # This register corresponds to gyro_y
            12: sp.RACProtocol.INT,  # This register corresponds to gyro_z

        },
        'name': {
            'drive_delay1': 0,
            'drive_delay2': 1,
            'drive_enable1': 2,
            'drive_enable2': 3,
            'step_counter1': 4,
            'step_counter2': 5,
            'transmit_rate': 6,
            'acc_x': 7,
            'acc_y': 8,
            'acc_z': 9,
            'gyro_x': 10,
            'gyro_y': 11,
            'gyro_z': 12
        }
    }
    ard_link = ArduinoLink('127.0.0.1', 5000, 'COM3', 250000, register_map)
    ard_link.start()


if __name__ == '__main__':
    main()
