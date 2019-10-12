import logging

from common.logging import setup_logger
from market_interface.market_interface_template import MarketInterface

setup_logger('example_market_interface.log')


class TestMarketInterface (MarketInterface):
    def __init__(self):
        MarketInterface.__init__(self, market_interface_id="TEST_INTERFACE")
        self.logger = logging.getLogger('test_market_interface')
        self.logger.info("TEST MARKET INTERFACE INITIALIZED")

    def make_rest_request(self):
        pass

    def create_websocket_stream(self):
        pass

    def send_websocket_command(self, websocket, payload):
        pass

    def on_websocket_recv(self, msg):
        pass

    def interface_main_cycle(self):
        last_subs = None
        while True:
            if last_subs != self.subscriptions:
                print("Subscriptions:")
                for sub in self.subscriptions:
                    print("%r" % sub)
                last_subs = self.subscriptions.copy()


test_interface = TestMarketInterface()
