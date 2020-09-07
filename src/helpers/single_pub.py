import proccom
import time


def format_msg():
    return {'transmit_rate': 500, 'drive_delay1': 1000, 'drive_delay2': 1000, 'drive_enable1': False, 'drive_enable2': False}


def main():
    publisher = proccom.Publisher('arduino_cmd', 'test_pub', format_msg)
    publisher.connect()
    time.sleep(1)
    publisher.publish()
    time.sleep(1)
    publisher.stop()


if __name__ == '__main__':
    main()
