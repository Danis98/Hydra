import json
import time
import logging

from common.logging import setup_logger

from portfolio_manager.portfolio_api import PortfolioApiServer
from portfolio_manager.strategy_lifecycle import init, start, stop

setup_logger('portfolio_manager.log')


class PortfolioManager:
    """
    Manages the whole Hydra system.
    Keeps a list of market interfaces and strategies, and assigns resources.
    It also send initialization and various lifecycle signals to the strategy.
    Starts a server which handles incoming requests to the manager.
    """
    def __init__(self, config_file="config.json"):
        """
        Initialize manager and start manager server
        :param config_file: filename of the config file containing the necessary info
        """
        self.logger = logging.getLogger('portfolio_manager')
        self.logger.info('Starting portfolio manager...')

        # read config file
        self.config = json.loads(open(config_file, "r").read())

        self.logger.debug('Config loaded')

        self.HOST = self.config['host']
        self.PORT = self.config['port']
        self.REFRESH_TIMEOUT = self.config['refresh_timeout']

        self.TEST_MONEY_AMOUNT = 1000

        # registered strategies, indexed by ID
        # entry contains:
        #   strategy_id: ID of the strategy
        #   address: address of the strategy server handling incoming messages
        #   port: port of server
        #   status: current status of the strategy
        #   allocated_resources: resources allocated to the strategy to work with
        self.strategies = {}
        # registered market interfaces, usually one,
        # more for load balancing and different data sources
        # indexed by ID, entry contains:
        #   address: address of the interface server handling incoming messages
        #   port: port of the server
        self.market_interfaces = {}

        # set to true to kill main process
        self.stop_manager = False

        # start manager server
        try:
            self.logger.debug('Starting server...')
            portfolio_server = PortfolioApiServer(self.HOST,
                                                  self.PORT,
                                                  self)
            portfolio_server.start()
        except Exception as e:
            self.logger.error('Could not start server: %s' % e)
            exit(1)

        self.logger.info('Manager setup complete')

    def manager_main_cycle(self):
        """
        Cycle that periodically checks registered strategies and interfaces.
        Handles sending lifecycle signals, resource reallocation commands and
        in the future pings to check availability.
        """
        last_strats = None
        last_interfs = None
        while not self.stop_manager:
            # debug, when strategies or interfaces structs change print them
            if last_interfs != self.market_interfaces or last_strats != self.strategies:
                print("Strategies: %r" % self.strategies)
                print("Interfaces: %r" % self.market_interfaces)
                last_strats = self.strategies.copy()
                last_interfs = self.market_interfaces.copy()

            # iterate over strategies, check up on them
            for strat_id in self.strategies:
                strategy = self.strategies[strat_id]
                # try to initialize idle strategies
                if strategy['status'] == 'IDLE':
                    # initialize strategy with test amount of money
                    strategy['allocated_resources'] = self.TEST_MONEY_AMOUNT
                    if init(address=strategy['address'],
                            port=strategy['port'],
                            resources=strategy['allocated_resources']):
                        strategy['status'] = 'INITIALIZING'
                elif strategy['status'] == 'INITIALIZING':
                    # TODO define behavior if strategy is initializing
                    pass
                elif strategy['status'] == 'RUNNING':
                    # TODO define behavior if strategy is running
                    pass

            time.sleep(self.REFRESH_TIMEOUT)


# start manager
manager = PortfolioManager()
manager.manager_main_cycle()
