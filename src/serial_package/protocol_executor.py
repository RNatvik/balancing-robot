import serial
import threading


class ProtocolExecutor:
    """
    The protocol executor is a class that is used to implement different serial protocols.
    It handles exceptions related to the serial port. The protocol is expected to handle all other exceptions.
    The protocol must have a receive(port: serial.Serial) method and a transmit(port: serial.Serial, data) method.
    The ProtocolExecutor class is designed with multithreading in mind and initializes a transmit thread and a receive
    thread. These threads will be synchronized by locks and events. To transmit a message use the set_data(data, block)
    function.
    """

    def __init__(self, protocol, input_handler, com_port, baudrate, *args, debug=False, **kwargs):
        """
        Constructs a protocol executor

        :param protocol: an instance of the desired protocol class
        :param input_handler: a method for handling incoming data.
        :param com_port: the port of the serial device
        :param baudrate: the baudrate of the serial device
        :param args: additional arguments for the input_handler function
        :param debug: print debug info to terminal
        :param kwargs: additional keyword arguments for the input_handler function
        """
        self.protocol = protocol
        self.input_handler = input_handler
        self.debug = debug
        self.args = args
        self.kwargs = kwargs

        self.recv_thread = threading.Thread(target=self._run_recv)
        self.trans_thread = threading.Thread(target=self._run_trans)
        self.serial_port = serial.Serial()
        self.serial_port.port = com_port
        self.serial_port.baudrate = baudrate

        self.port_lock = threading.Lock()
        self.output_lock = threading.Lock()
        self.output_event = threading.Event()

        self.shutdown = False
        self.output_data = None

    def start(self):
        """
        Starts the protocol executor threads and open the serial port
        :return: None
        """
        try:
            self.shutdown = False
            self.serial_port.open()
            self.recv_thread.start()
            self.trans_thread.start()
            success = True
        except serial.SerialException as e:
            self.stop()
            success = False
            if self.debug:
                print(self, f' :: {e}')
        return success

    def stop(self):
        self.shutdown = True
        self.output_event.set()
        if self.debug:
            print(self, ":: Shutdown sequence has been initialized")

    def set_data(self, data, block=False):
        if block:
            while self.output_event.is_set():
                pass
        with self.output_lock:
            self.output_data = data
        self.output_event.set()

    def _run_recv(self):
        while not self.shutdown:
            try:
                if self.serial_port.inWaiting() > 0:
                    with self.port_lock:
                        data = self.protocol.receive(self.serial_port)
                        self.input_handler(data, *self.args, **self.kwargs)
            except serial.SerialException as e:
                self.stop()
                if self.debug:
                    print(self, f' :: {e}')

    def _run_trans(self):
        while not self.shutdown:
            try:
                event = self.output_event.wait()
                if event and not self.shutdown:
                    with self.output_lock:
                        data = self.output_data
                        self.output_event.clear()
                    with self.port_lock:
                        self.protocol.transmit(self.serial_port, data)
            except serial.SerialException as e:
                self.stop()
                if self.debug:
                    print(self, f' :: {e}')
