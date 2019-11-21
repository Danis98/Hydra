import time
import logging
import matplotlib.pyplot as plt

from common.logging import setup_logger
from strategy.strategy_template import Strategy
from common.plot_manager import PlotManager

setup_logger('example_strategy.log')

MAX_PLOT_POINTS = 200


class ExampleStrategy (Strategy):
    funds = 0

    def __init__(self):
        Strategy.__init__(self, strategy_id='TEST_STRATEGY', mode='TEST_LIVE', config_file='config.json')
        self.logger = logging.getLogger('example_strategy')

        self.symbol_data = []

        self.plot_manager = PlotManager(max_elements=MAX_PLOT_POINTS)

        self.plot_manager.add_subplot('data_plot', 111)
        self.plot_manager.set_subplot_title('data_plot', 'Incoming Data')

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

        self.subscribe('TEST_INTERFACE', 'RANDOM', 1)

    def on_start(self, data):
        super().on_start(data)

    def on_stop(self, data):
        super().on_stop(data)

    def on_funds_reallocation(self, data):
        super().on_funds_reallocation(data)

    def on_data_feed_recv(self, data):
        self.symbol_data.append(data['value'])

    def strategy_cycle(self):
        last_status = None
        last_plotted = 0
        while self.RUN:
            if last_status != self.STATUS:
                self.logger.info("Test strategy is %s" % self.STATUS)
                last_status = self.STATUS

            if len(self.symbol_data) > last_plotted:
                for i in range(last_plotted, len(self.symbol_data)):
                    if i == 0:
                        self.plot_manager.add_line('data_plot', 'price_line', [0], self.symbol_data[0:1])
                    else:
                        self.plot_manager.append_datapoint('data_plot', i+1, {
                            'price_line': self.symbol_data[i]
                        })
                last_plotted = len(self.symbol_data)


test_strategy = ExampleStrategy()
test_strategy.run()
