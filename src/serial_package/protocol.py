import struct
import serial


class RACProtocol:
    """
    The RAC (Register Access Control) protocol is based on linking value registers between units.
    Registers start at 0 and has a value type associated with each register. Units communicating using this protocol
    must agree on which register has which value type and represents a given variable.
    To transmit a message the sender specifies 1 byte corresponding to which register to write to, and 'n' bytes
    corresponding to the byte value of that value. Depending on implementation on secondary unit, there is an option
    to transmit / receive start and end bytes as well.

    TODO: Maybe add default com error register?
    If receiving a byte representing a register not in use, transmit back an error detected flag and discard the current message?
    """
    BOOL = 0
    BYTE = 1
    INT = 2
    FLOAT = 3
    LONG = 4
    UINT = 5
    ULONG = 6

    # _START and _END has both the byte and int version of their values available for an "if .. in .." statement
    _START = (b'\xff', 0xff)
    _END = (b'\xfe', 0xfe)

    def __init__(self, register_type_map: dict, input_pad=False, output_pad=False):
        """
        Constructor for the protocol object.
        The register_type_map is a dictionary mapping register ID (as int) to a value type (i.e bool, byte, int etc)

        :param register_type_map: a dictionary mapping registers to variable types
        :param input_pad: determine if the receive method expects start and stop bytes.
        :param output_pad: determines whether to transmit start and stop bytes.
        """
        self.register_map = register_type_map
        self.parser_map = {
            RACProtocol.BOOL: (1, '?'),
            RACProtocol.BYTE: (1, 'B'),
            RACProtocol.INT: (2, 'h'),
            RACProtocol.FLOAT: (4, 'f'),
            RACProtocol.LONG: (4, 'l'),
            RACProtocol.UINT: (2, 'H'),
            RACProtocol.ULONG: (4, 'L')
        }
        self.input_pad = input_pad
        self.output_pad = output_pad

    def receive(self, port: serial.Serial):
        """
        Receives values from the Serial port.
        This method will either read a single register (if self.input_pad == False) or read multiple values between a
        defined start and stop byte.

        :param port: The serial.Serial port object from which to read
        :return: a list of register value pairs [(register1, value1), (register2, value2)]
        """
        return_values = []
        if self.input_pad:
            read = port.read(1) in RACProtocol._START
            while read:
                register = self._read_register(port)
                if register in RACProtocol._END:
                    read = False
                else:
                    value = self._read_value(port, register)
                    return_values.append((register, value))
        else:
            register = self._read_register(port)
            value = self._read_value(port, register)
            return_values.append((register, value))
        return return_values

    def _read_register(self, port):
        """
        Helper method for when reading register bytes
        port.read() returns bytes object, but must be int for easier comparison to others

        :param port: the port to read from
        :return: the register value as int
        """
        register = port.read(1)
        return struct.unpack('B', register)[0]

    def _read_value(self, port, register):
        """
        Reads the serial port for the values corresponding to 'register'.

        :param port: the serial port
        :param register: the register determining how many bytes will be read and the output value type
        :return: the read value as a value type corresponding to the register.
        """
        register_type = self.register_map[register]
        num_to_read = self.parser_map[register_type][0]
        byte_data = port.read(num_to_read)
        value = struct.unpack(self.parser_map[register_type][1], byte_data)[0]
        return value

    def transmit(self, port: serial.Serial, data: list):
        """
        Transmits the information contained in "data" over the serial port port.

        :param port: the serial port
        :param data: A list containing tuples of register value pairs: [(register1, value1), (register2, value2), ...]
        :return:
        """
        msg = b''
        for register, value in data:
            register_type = self.register_map[register]
            msg += struct.pack(self.parser_map[RACProtocol.BYTE][1], register)
            msg += struct.pack(self.parser_map[register_type][1], value)
        if self.output_pad:
            msg = RACProtocol._START[0] + msg + RACProtocol._END[0]
        port.write(msg)
