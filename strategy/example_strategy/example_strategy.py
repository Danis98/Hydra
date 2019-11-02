import time
import logging
import matplotlib.pyplot as plt

from common.logging import setup_logger
from strategy.strategy_template import Strategy

setup_logger('example_strategy.log')


class ExampleStrategy (Strategy):
    funds = 0

    def __init__(self):
        Strategy.__init__(self, strategy_id='TEST_STRATEGY', mode='TEST_LIVE', config_file='config.json')
        self.logger = logging.getLogger('example_strategy')

        self.symbol_data = []

        self.logger.info('Example strategy initialized')

    def run(self):
        self.logger.info('Starting example strategy...')
        self.boot()
        self.logger.info('Shutting down example strategy...')

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

    def on_data_feed_recv(self, data):
        self.symbol_data.append(data['value'])
        self.logger.info(self.symbol_data)

    def strategy_cycle(self):
        plt.ion()
        fig = plt.figure()
        ax = fig.add_subplot(111)
        line, = ax.plot([], [], 'r-')

        last_status = None
        while self.RUN:
            if last_status != self.STATUS:
                self.logger.info("Test strategy is %s" % self.STATUS)
                last_status = self.STATUS

            if len(self.symbol_data) > 0:
                line.set_xdata(range(len(self.symbol_data)))
                line.set_ydata(self.symbol_data)
                plt.draw()
                plt.pause(0.02)
            time.sleep(3)
        plt.ioff()
        plt.show()


test_strategy = ExampleStrategy()
test_strategy.run()
