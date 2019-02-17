import sys
import json
import time
import string
import socket
import random
import logging
import threading

logger = logging.getLogger('market_interface')

BUFFER_SIZE = 2048


class WebsocketHandler (threading.Thread):
    def __init__(self):
        threading.Thread.__init__(self)

    def run(self):
        pass


class MarketInterfaceRequestHandler (threading.Thread):
    def __init__(self, client_socket, interface):
        threading.Thread.__init__(self)

        self.socket = client_socket
        self.INTERFACE = interface

    def run(self):
        logger.debug('Handling request')
        request = json.loads(self.socket.recv(BUFFER_SIZE).decode())
        # decide which handler function to call
        if request['query'] == 'INTERFACE_SUBSCRIBE':
            self.handle_subscription(request['data'])
        else:
            logger.error('Unknown request: %s' % request['query'])
            resp = {
                'status': 'FAIL',
                'message': 'API query not defined'
            }
            self.socket.send(json.dumps(resp).encode())

    def handle_subscription(self, data):
        logger.info("Subscription request received from %s" % data['strategy_id'])
        rand_str = ''.join(random.choices(string.ascii_letters + string.digits, k=16))
        sub_handle = "%s_%s_%s:%s" % (self.INTERFACE.INTERFACE_ID, data['symbol'], data['strategy_id'], rand_str)
        self.INTERFACE.subscriptions[sub_handle] = {
            'strategy_address': data['strategy_address'],
            'strategy_port': data['strategy_port'],
            'symbol': data['symbol'],
            'frequency': data['frequency']
        }

        data_sender = threading.Thread(target=self.INTERFACE.push_feed,
                                       args=(sub_handle,))
        data_sender.start()

    def handle_bulk_data_request(self, data):
        pass

    def handle_order(self, data):
        pass


class MarketInterfaceServer (threading.Thread):
    def __init__(self, host, port, interface):
        threading.Thread.__init__(self)
        self.HOST = host
        self.PORT = port
        self.INTERFACE = interface

        self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.socket.bind((self.HOST, self.PORT))
        self.socket.listen(5)

        logger.info('Interface server started successfully')

    # accept connections and handle them in their own thread
    def run(self):
        while True:
            (client_socket, address) = self.socket.accept()
            logger.info('Accepted connection: %r' % (address,))
            handler = MarketInterfaceRequestHandler(client_socket, self.INTERFACE)
            handler.start()


class MarketInterface:
    def __init__(self, market_interface_id):
        self.INTERFACE_ID = market_interface_id

        # load initial config
        self.config = json.loads(open('config.json', 'r').read())

        self.HOST = self.config['host']
        self.PORT = self.config['port']
        self.MANAGER_ADDRESS = self.config['manager_address']
        self.MANAGER_PORT = self.config['manager_port']

        self.subscriptions = {}

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

    def push_feed(self, subscription_handle):
        strategy_address = self.subscriptions[subscription_handle]['strategy_address']
        strategy_port = self.subscriptions[subscription_handle]['strategy_port']
        timeout = self.subscriptions[subscription_handle]['frequency']
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        try:
            s.connect((strategy_address, strategy_port))
        except ConnectionRefusedError:
            logger.error('Could not connect to strategy')
            return

        while subscription_handle in self.subscriptions:
            query = {
                'query': 'MARKET_DATA_FEED',
                'data': {
                    'message': 'TEST'
                }
            }

            try:
                s.send(json.dumps(query).encode())

            except socket.timeout:
                logger.error('Connection timed out with strategy during feed push')
            time.sleep(timeout)

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
