import sys
import json
import logging

from common.messaging import message_to_address
from market_interface.market_interface_api import MarketInterfaceApiServer


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
        self.logger = logging.getLogger('market_interface')
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

        self.interface_server = None

    def boot(self):
        """
        Start all the processes and do all the things needed to start rollin'
        """
        self.register()

        # start interface server
        interface_server = MarketInterfaceApiServer(self.HOST, self.PORT, self)
        interface_server.start()

        # start interface main cycle
        self.interface_main_cycle()

    def register_callback(self, resp):
        if resp['status'] == 'SUCCESS':
            self.logger.info('Interface registered')
        else:
            self.logger.error('Could not register interface: %s', resp['message'])
            sys.exit(1)

    def register(self):
        # send registration request
        query = {
            'query': 'REGISTER_MARKET_INTERFACE',
            'data': {
                'market_interface_id': self.INTERFACE_ID,
                'market_interface_address': self.HOST,
                'market_interface_port': self.PORT,
            }
        }

        # send registration request to manager in this thread, since it is vital for everything
        message_to_address(self.MANAGER_ADDRESS,
                           self.MANAGER_PORT,
                           query,
                           True,
                           self.register_callback)

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

    def get_data(self, sub_handle):
        pass
