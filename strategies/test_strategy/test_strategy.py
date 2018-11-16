import json
import time
import logging
# noinspection PyUnresolvedReferences
from strategy_template import Strategy

logging.basicConfig(filename='test_strategy.log', filemode='w', level=logging.DEBUG)
logging.getLogger().setLevel(logging.INFO)
logging.getLogger().addHandler(logging.StreamHandler())
logger = logging.getLogger('test_strategy')


class TestStrategy (Strategy):
    funds = 0

    def __init__(self):
        logger.info('Starting test strategy...')
        Strategy.__init__(self, strategy_id='TEST_STRATEGY', mode='TEST_RANDOM')

    def on_init(self, params):
        logger.info('Initializing!')
        self.STATUS = 'INITIALIZING'
        self.funds = params['resources']
        self.subscribe('TEST_INTERFACE', 'RANDOM', 10)

    def on_start(self, params):
        pass

    def on_stop(self, params):
        pass

    def on_funds_reallocation(self, params):
        pass

    def strategy_cycle(self):
        last_status = None
        while self.RUN:
            if last_status != self.STATUS:
                logger.info("Test strategy is %s" % self.STATUS)
                last_status = self.STATUS
            time.sleep(5)


test_strategy = TestStrategy()
