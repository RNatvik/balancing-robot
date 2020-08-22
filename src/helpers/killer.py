import proccom
import threading
import time

def msg_format(value):
    return value


def main(target, host='127.0.0.1', port=5000, delay=2):

    publisher = proccom.Publisher('shutdown_cmd', 'killer', msg_format, host=host, port=port)
    publisher.connect()
    timer = threading.Timer(delay, publisher.publish, args=[{'name': target, 'value': True}])
    timer.start()
    print('end of main')


if __name__ == '__main__':
    hosts = [
        'arduino_link_sub', 'feedback_sub', 'server'
    ]
    for target in hosts:
        main(target)
        time.sleep(5)
