import proccom
import time


def format_msg():
    return {'transmit_rate': 100}


def main():
    publisher = proccom.Publisher('arduino_cmd', 'test_pub', format_msg)
    publisher.connect()
    time.sleep(1)
    publisher.publish()
    time.sleep(1)
    publisher.stop()


if __name__ == '__main__':
    main()
