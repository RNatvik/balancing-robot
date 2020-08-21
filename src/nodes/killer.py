import proccom
import threading


def msg_format(value):
    return value


def main(host='127.0.0.1', port=5000, delay=5):
    publisher = proccom.Publisher('shutdown_cmd', 'killer', msg_format, host=host, port=port)
    publisher.connect()
    timer = threading.Timer(5, publisher.publish, args=[True])
    timer.start()
    print('end of main')


if __name__ == '__main__':
    main()
