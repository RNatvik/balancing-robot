import json

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


def main(server_config_path, delay=2):
    with open(server_config_path, 'r') as server_file:
        server_config = json.load(server_file)
    host = server_config['host']
    port = server_config['port']
    app = ServerApp(host, port)
    app.run(delay)


if __name__ == '__main__':
    main('../config/server.json')
