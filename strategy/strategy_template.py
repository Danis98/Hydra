import sys
import json
import socket
import logging
import threading

from strategy.strategy_api import StrategyApiServer


class Strategy:
    """
    Basic framework for strategy, takes care of communication with the Hydra system under
    the hood.
    Exposes endpoints for the specific strategy implementations to override, mostly for
    incoming command or data feed handling.
    """
    def __init__(self, strategy_id, mode, config_file="config.json"):
        """
        Initializes strategy, registering it with the portfolio manager and starting the
        strategy-specific main cycle when it's done.

        :param strategy_id: identifying ID of the strategy
        :param mode: mode of operation, determines how the strategy is handled
        :param config_file: filename of the configuration file

        Modes of operation (NOT YET IMPLEMENTED):
            REAL: orders get routed to real exchange, strategy handles real resources
            TEST_LIVE: mock orders, live real data from market
            TEST_HISTORICAL: mock orders, data is supplied as in TEST_LIVE but from historical sources
        """
        # TODO: implement backtest mode and real mode
        self.logger = logging.getLogger('strategy_framework')

        # set false to kill strategy
        self.RUN = True

        # load config
        self.config = json.loads(open(config_file, 'r').read())
        self.STRATEGY_ID = strategy_id
        self.MODE = mode
        self.STATUS = 'IDLE'
        self.HOST = self.config['host']
        self.PORT = self.config['port']
        self.MANAGER_ADDRESS = self.config['manager_address']
        self.MANAGER_PORT = self.config['manager_port']

        self.allocated_funds = 0

        # active subscriptions
        self.subscriptions = {}

        # register strategy with manager
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        try:
            s.connect((self.MANAGER_ADDRESS, self.MANAGER_PORT))
        except ConnectionRefusedError:
            self.logger.error('Could not connect to manager')
            sys.exit()

        query = {
            'query': 'REGISTER_STRATEGY',
            'data': {
                'strategy_id': self.STRATEGY_ID,
                'strategy_address': self.HOST,
                'strategy_port': self.PORT,
                'mode': self.MODE,
            }
        }
        # send registration request to manager
        try:
            s.send(json.dumps(query).encode())
            resp = json.loads(s.recv(1024).decode())

            if resp['status'] == 'FAIL':
                self.logger.error('Could not register strategy: %s', resp['message'])
                sys.exit()
            elif resp['status'] == 'SUCCESS':
                self.logger.info('Strategy registered')
        except socket.timeout:
            self.logger.error('Connection timed out with manager during registration')
            sys.exit()

        # start listening server
        self.strategy_server = StrategyApiServer(self.HOST, self.PORT, self)
        self.strategy_server.start()

        # start main strategy
        self.strategy_cycle()

    ##################################
    #        MARKET INTERFACE        #
    ##################################

    def send_manager_query(self, manager_address, manager_port, query, callback_success, callback_fail):
        """
        Handles sending the request to the manager, then calls the appropriate callback.
        Usually used to send requests in a non-blocking way, by executing it in a separate thread.

        :param manager_address: address of the manager server
        :param manager_port: port of the server
        :param query: body of the request
        :param callback_success: function to call in case of success
        :param callback_fail: function to call in case of failure
        """
        # connect to manager
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        try:
            s.connect((manager_address, manager_port))
        except ConnectionRefusedError:
            self.logger.error('Could not connect to manager')
            resp = {
                'status': 'FAIL',
                'message': 'Could not connect to manager'
            }
            callback_fail(resp)
            return

        # send request
        try:
            s.send(json.dumps(query).encode())
            resp = json.loads(s.recv(1024).decode())

            # call appropriate callback
            if resp['status'] == 'FAIL':
                callback_fail(resp)
            elif resp['status'] == 'SUCCESS':
                callback_success(resp)

        except socket.timeout:
            self.logger.error('Connection timed out with manager during request')
            resp = {
                'status': 'FAIL',
                'message': 'Connection timed out with manager during request'
            }
            callback_fail(resp)
            return

    def subscribe(self, market_interface_id, symbol, frequency):
        """
        Subscribe to data feed.

        :param market_interface_id: ID of the desired market interface
        :param symbol: requested symbol
        :param frequency: number of seconds between feed messages
        """
        self.logger.info("Subscribing to %s:%s..." % (market_interface_id, symbol))
        query = {
            'query': 'SUBSCRIBE',
            'data': {
                'strategy_id': self.STRATEGY_ID,
                'market_interface_id': market_interface_id,
                'symbol': symbol,
                'frequency': frequency
            }
        }

        def subscribe_fail(resp):
            self.logger.error('Could not subscribe to data feed: %s', resp['message'])

        def subscribe_success(resp):
            self.logger.info('Subscribed to data feed successfully')
            sub_handle = resp['data']['subscription_handle']
            self.subscriptions[sub_handle] = {
                'market_interface_id': market_interface_id
            }

        # send subscription request to manager in separate thread
        handler = threading.Thread(target=self.send_manager_query,
                                   args=(self.MANAGER_ADDRESS,
                                         self.MANAGER_PORT,
                                         query,
                                         subscribe_success,
                                         subscribe_fail))
        handler.start()

    def unsubscribe(self, subscription_handle):
        """
        Unsubscribe from feed

        :param subscription_handle: handle of the deleted subscription
        """
        self.logger.info("Unsubscribing from %s..." % subscription_handle)

        market_interface_id = self.subscriptions[subscription_handle]['market_interface_id']
        query = {
            'query': 'UNSUBSCRIBE',
            'data': {
                'strategy_id': self.STRATEGY_ID,
                'market_interface': market_interface_id,
                'subscription_handle': subscription_handle
            }
        }

        def unsubscribe_fail(resp):
            self.logger.error('Could not unsubscribe to data feed: %s', resp['message'])

        def unsubscribe_success(resp):
            self.logger.info('Unsubscribed to data feed successfully')
            del self.subscriptions[subscription_handle]

        # send subscription request to manager in separate thread
        handler = threading.Thread(target=self.send_manager_query,
                                   args=(self.MANAGER_ADDRESS,
                                         self.MANAGER_PORT,
                                         query,
                                         unsubscribe_success,
                                         unsubscribe_fail))
        handler.start()

    def unsubscribe_all(self):
        """Shortcut function, unsubscribe from all data feeds"""
        for sub in self.subscriptions:
            self.unsubscribe(sub['subscription_handle'])

    def get_bulk_data(self, market_interface_id, symbol, start_time, end_time, frequency):
        pass

    def get_current_data(self, market_interface_id, symbol):
        pass

    ##################################
    #        STRATEGY METHODS        #
    ##################################

    """
    The following methods are to be overridden by the specific strategy using this template.
    """

    def strategy_cycle(self):
        """Main strategy body, should contain cycle with algorithm logic"""
        pass

    # lifecycle functions

    def on_init(self, data):
        """Called when initialization command is received from the manager"""
        pass

    def on_start(self, data):
        """Called when start command is received from the manager"""
        pass

    def on_stop(self, data):
        """Called when stop command is received from the manager"""
        pass

    # event handlers

    def on_funds_reallocation(self, data):
        """Called when manager sends fund reallocation command, strategy should resize its positions"""
        pass

    def on_data_feed_recv(self, data):
        """Called when the strategy receives a data feed message from one of its subscriptions"""
        pass
