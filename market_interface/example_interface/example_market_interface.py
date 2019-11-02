import logging
import random
import time

from common.logging import setup_logger
from market_interface.market_interface_template import MarketInterface

setup_logger('example_market_interface.log')


class ExampleMarketInterface (MarketInterface):
    def __init__(self):
        MarketInterface.__init__(self, market_interface_id="TEST_INTERFACE")
        self.logger = logging.getLogger('test_market_interface')
        self.logger.debug("Example market interface initialized")

    def run(self):
        self.logger.info("Starting example market interface")
        self.boot()
        self.logger.info("Interface shutting down")

    def make_rest_request(self):
        pass

    def create_websocket_stream(self):
        pass

    def send_websocket_command(self, websocket, payload):
        pass

    def on_websocket_recv(self, msg):
        pass

    def interface_main_cycle(self):
        self.rand_cur_value = 100
        last_subs = None
        while True:
            if last_subs != self.subscriptions:
                self.logger.info("Subscriptions:")
                for sub in self.subscriptions:
                    self.logger.info("%r" % sub)
                last_subs = self.subscriptions.copy()
            self.rand_cur_value += 2 * random.random() - 1
            time.sleep(1)

    def get_data(self, sub_handle):
        symbol = self.subscriptions[sub_handle]['symbol']
        if symbol == 'RANDOM':
            return {
                'value': self.rand_cur_value
            }
        else:
            return None


test_interface = ExampleMarketInterface()
test_interface.run()
