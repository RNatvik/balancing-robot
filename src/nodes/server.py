import proccom
import threading


class ServerApp:

    def __init__(self, host, port):
        self.server = proccom.Server(host, port)
        self.subscriber = proccom.Subscriber({'shutdown_cmd': self.callback}, 'server', host=host, port=port)

    def callback(self, msg):
        data = msg['data']
        name = data['name']
        if name == self.subscriber.id:
            shutdown = data['value']
            if shutdown:
                self.server.stop()
                self.subscriber.stop()
                print('Shutdown cmd received, server shutdown initialized')

    def run(self, delay=5):
        timer = threading.Timer(delay, self.subscriber.connect)
        timer.start()
        self.server.start()  # Blocking call


def main(host='127.0.0.1', port=5000, delay=5):
    app = ServerApp(host, port)
    app.run(delay)


if __name__ == '__main__':
    main()
