import sys
import json
import socket
import logging
import threading

from market_interface.market_interface_api import MarketInterfaceServer


logger = logging.getLogger('market_interface')


# TODO: move to separate file, along with other client-side handlers
class WebsocketHandler (threading.Thread):
    def __init__(self):
        threading.Thread.__init__(self)

    def run(self):
        pass


class MarketInterface:
    """
    Provides connection with the outside world, in the form of data feeds and
    order execution.
    Market interfaces have primarily two tasks:
        Provide data feeds to subscribers (could be market data, news, etc...)
        Execute orders on behalf of strategies (not necessarily available on all interfaces)
    """
    def __init__(self, market_interface_id, config_file="config.json"):
        """
        Initialize market interface, register it with the manager and start the server

        :param market_interface_id: ID of the market interface
        :param config_file: file containing necessary init parameters
        """
        self.INTERFACE_ID = market_interface_id

        # load initial config
        self.config = json.loads(open(config_file, 'r').read())
        self.HOST = self.config['host']
        self.PORT = self.config['port']
        self.MANAGER_ADDRESS = self.config['manager_address']
        self.MANAGER_PORT = self.config['manager_port']
        self.BUFFER_SIZE = self.config['buffer_size']

        # active subscriptions, indexed by their unique handle
        self.subscriptions = {}

        # connect to the manager
        manager_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        try:
            manager_sock.connect((self.MANAGER_ADDRESS, self.MANAGER_PORT))
        except ConnectionRefusedError:
            logger.error('Could not connect to manager')
            sys.exit()

        # send registration request
        query = {
            'query': 'REGISTER_MARKET_INTERFACE',
            'data': {
                'market_interface_id': self.INTERFACE_ID,
                'market_interface_address': self.HOST,
                'market_interface_port': self.PORT,
            }
        }
        try:
            manager_sock.send(json.dumps(query).encode())
            resp = json.loads(manager_sock.recv(1024).decode())

            # TODO: implement retry
            if resp['status'] == 'FAIL':
                logger.error('Could not register interface: %s', resp['message'])
                sys.exit()
            elif resp['status'] == 'SUCCESS':
                logger.info('Interface registered')
        except socket.timeout:
            logger.error('Connection timed out with manager during registration')
            sys.exit()

        # start interface server
        interface_server = MarketInterfaceServer(self.HOST, self.PORT, self)
        interface_server.start()

        # start interface main cycle
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
