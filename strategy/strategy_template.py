import sys
import json
import logging
import threading

from common.messaging import message_to_address
from strategy.strategy_api import StrategyApiServer

lock = threading.Lock()


class Strategy:
    """
    Basic framework for strategy, takes care of communication with the Hydra system under
    the hood.
    Exposes endpoints for the specific strategy implementations to override, mostly for
    incoming command or data feed handling.
    """
    def __init__(self, strategy_id, mode, config_file):
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
        try:
            self.config = json.loads(open('config.json').read())
        except FileNotFoundError:
            self.logger.error('Could not find config file %s, aborting...' % config_file)
            sys.exit(1)
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

        # server listening to incoming queries
        self.strategy_server = None

    def boot(self):
        """
        Start all the processes and do all the things needed to start rollin'
        """
        # register strategy with manager
        self.register()

        # start listening server
        self.strategy_server = StrategyApiServer(self.HOST, self.PORT, self)
        self.strategy_server.start()

        # start main strategy body
        self.strategy_cycle()

    def register_callback(self, resp):
        if resp['status'] == 'SUCCESS':
            self.logger.info('Strategy registered')
        else:
            self.logger.error('Could not register strategy: %s', resp['message'])
            sys.exit(1)

    def register(self):
        """
        Register strategy with manager
        """
        query = {
            'query': 'REGISTER_STRATEGY',
            'data': {
                'strategy_id': self.STRATEGY_ID,
                'strategy_address': self.HOST,
                'strategy_port': self.PORT,
                'mode': self.MODE,
            }
        }

        # send registration request to manager in this thread, since it is vital for everything
        message_to_address(self.MANAGER_ADDRESS,
                           self.MANAGER_PORT,
                           query,
                           True,
                           self.register_callback)

    ##################################
    #        MARKET INTERFACE        #
    ##################################

    def subscribe_callback(self, resp, market_interface_id):
        if resp['status'] == 'SUCCESS':
            self.logger.info('Subscribed to data feed successfully')
            sub_handle = resp['data']['subscription_handle']
            self.subscriptions[sub_handle] = {
                'market_interface_id': market_interface_id
            }
        else:
            self.logger.error('Could not subscribe to data feed: %s' % resp['message'])

    def subscribe(self, market_interface_id, symbol, frequency):
        """
        Subscribe to data feed.

        :param market_interface_id: ID of the desired market interface
        :param symbol: requested symbol
        :param frequency: number of seconds between feed messages
        """
        self.logger.info("Subscribing to %s:%s..." % (market_interface_id, symbol))
        query = {
            'query': 'INTERFACE_SUBSCRIBE',
            'data': {
                'strategy_id': self.STRATEGY_ID,
                'market_interface_id': market_interface_id,
                'symbol': symbol,
                'frequency': frequency
            }
        }

        # send subscription request to manager in separate thread
        handler = threading.Thread(target=message_to_address,
                                   args=(self.MANAGER_ADDRESS,
                                         self.MANAGER_PORT,
                                         query,
                                         True,
                                         lambda resp: self.subscribe_callback(resp, market_interface_id)))
        handler.start()

    def unsubscribe_callback(self, resp, subscription_handle):
        if resp['status'] == 'SUCCESS':
            self.logger.info('Unsubscribed to data feed successfully')
            del self.subscriptions[subscription_handle]
        else:
            self.logger.error('Could not unsubscribe to data feed: %s' % resp['message'])

    def unsubscribe(self, subscription_handle):
        """
        Unsubscribe from feed

        :param subscription_handle: handle of the deleted subscription
        """
        self.logger.info("Unsubscribing from %s..." % subscription_handle)

        market_interface_id = self.subscriptions[subscription_handle]['market_interface_id']
        query = {
            'query': 'INTERFACE_UNSUBSCRIBE',
            'data': {
                'strategy_id': self.STRATEGY_ID,
                'market_interface': market_interface_id,
                'subscription_handle': subscription_handle
            }
        }

        # send subscription request to manager in separate thread
        handler = threading.Thread(target=message_to_address,
                                   args=(self.MANAGER_ADDRESS,
                                         self.MANAGER_PORT,
                                         query,
                                         True,
                                         lambda resp: self.subscribe_callback(resp, subscription_handle)))
        handler.start()

    def unsubscribe_all(self):
        """Shortcut function, unsubscribe from all data feeds"""
        all_subs = list(self.subscriptions.keys())
        for sub in all_subs:
            self.unsubscribe(sub)

    def get_bulk_data(self, market_interface_id, symbol, start_time, end_time, frequency):
        """
        Get data in bulk for a certain symbol during a certain time period.
        The market interface will send it in one, big response.
        Useful for getting historical data during setup.

        :param market_interface_id:
        :param symbol:
        :param start_time:
        :param end_time:
        :param frequency:
        :return:
        """
        pass

    def get_current_data(self, market_interface_id, symbol):
        """
        Get current snapshot of the data from the market interface. One time response.

        :param market_interface_id: ID of the concerned market interface
        :param symbol: requested symbol
        """
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
