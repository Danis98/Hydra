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
    def __init__(self):
        logger.info('Starting test strategy...')
        Strategy.__init__(self, strategy_name='test_strategy')

    def on_init(self, params):
        logger.info('Initializing!')
        self.STATUS = 'INITIALIZING'

test_strategy = TestStrategy()
