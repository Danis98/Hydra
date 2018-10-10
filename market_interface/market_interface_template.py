import sys
import json
import socket
import logging
import threading

logger = logging.getLogger('market_interface')


class WebsocketHandler (threading.Thread):
    def __init__(self):
        threading.Thread.__init__(self)

    def run(self):
        pass


class MarketInterfaceRequestHandler (threading.Thread):
    def __init__(self):
        threading.Thread.__init__(self)

    def run(self):
        pass

    def handle_subscription(self):
        pass

    def handle_bulk_data_request(self):
        pass

    def handle_order(self):
        pass


class MarketInterfaceServer (threading.Thread):
    def __init__(self, host, port, interface):
        threading.Thread.__init__(self)
        self.HOST = host
        self.PORT = port
        self.INTERFACE = interface

    def run(self):
        pass


class MarketInterface:
    def __init__(self, market_interface_id):
        self.INTERFACE_ID = market_interface_id

        # load initial config
        self.config = json.loads(open('config.json', 'r').read())

        self.HOST = self.config['host']
        self.PORT = self.config['port']
        self.MANAGER_ADDRESS = self.config['manager_address']
        self.MANAGER_PORT = self.config['manager_port']

        # register interface
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        try:
            s.connect((self.MANAGER_ADDRESS, self.MANAGER_PORT))
        except ConnectionRefusedError:
            logger.error('Could not connect to manager')
            sys.exit()

        query = {
            'query': 'REGISTER_MARKET_INTERFACE',
            'data': {
                'market_interface_id': self.INTERFACE_ID,
                'market_interface_address': self.HOST,
                'market_interface_port': self.PORT,
            }
        }
        try:
            s.send(json.dumps(query).encode())
            resp = json.loads(s.recv(1024).decode())

            if resp['status'] == 'FAIL':
                logger.error('Could not register interface: %s', resp['message'])
                sys.exit()
            elif resp['status'] == 'SUCCESS':
                logger.info('Interface registered')
        except socket.timeout:
            logger.error('Connection timed out with manager during registration')
            sys.exit()

        interface_server = MarketInterfaceServer(self.HOST, self.PORT, self)
        interface_server.start()

        self.interface_main_cycle()

    def interface_main_cycle(self):
        pass

    def make_rest_request(self):
        pass

    def create_websocket_stream(self):
        pass

    def send_websocket_command(self, websocket, payload):
        pass

    def on_websocket_recv(self, msg):
        pass
