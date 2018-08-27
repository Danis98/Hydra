import socket
import json
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
        Strategy.__init__(self, strategy_name='test_strategy', mode='TEST_RANDOM')

    def on_init(self, params):
        logger.info('Initializing!')
        self.STATUS = 'INITIALIZING'
        self.funds = params['resources']


test_strategy = TestStrategy()
