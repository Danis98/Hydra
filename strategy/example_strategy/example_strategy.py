import time
import json
import logging

from common.logging import setup_logger
from strategy.strategy_template import Strategy

setup_logger('example_strategy.log')


class ExampleStrategy (Strategy):
    funds = 0

    def __init__(self):
        Strategy.__init__(self, strategy_id='TEST_STRATEGY', mode='TEST_LIVE', config_file='config.json')
        self.logger = logging.getLogger('example_strategy')
        self.logger.info('Starting example strategy...')
        self.boot()

    def on_init(self, data):
        super().on_init(data)
        self.logger.info('Initializing!')
        self.STATUS = 'INITIALIZING'
        self.funds = data['resources']
        self.subscribe('TEST_INTERFACE', 'RANDOM', 3)

    def on_start(self, data):
        super().on_start(data)

    def on_stop(self, data):
        super().on_stop(data)

    def on_funds_reallocation(self, data):
        super().on_funds_reallocation(data)

    def strategy_cycle(self):
        last_status = None
        while self.RUN:
            if last_status != self.STATUS:
                self.logger.info("Test strategy is %s" % self.STATUS)
                last_status = self.STATUS
            time.sleep(5)


test_strategy = ExampleStrategy()
