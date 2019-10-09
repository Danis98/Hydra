import time
import json
import logging
from strategy.strategy_template import Strategy

logging.basicConfig(filename='example_strategy.log', filemode='w', level=logging.DEBUG)
logging.getLogger().setLevel(logging.INFO)
logging.getLogger().addHandler(logging.StreamHandler())
logger = logging.getLogger('example_strategy')


class ExampleStrategy (Strategy):
    funds = 0

    def __init__(self):
        logger.info('Starting test strategy...')
        config = json.loads(open('config.json').read())
        Strategy.__init__(self, strategy_id='TEST_STRATEGY', mode='TEST_LIVE', config=config)
        self.boot()

    def on_init(self, data):
        super().on_init(data)
        logger.info('Initializing!')
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
                logger.info("Test strategy is %s" % self.STATUS)
                last_status = self.STATUS
            time.sleep(5)


test_strategy = ExampleStrategy()
