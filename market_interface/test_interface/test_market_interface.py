import logging

from market_interface.market_interface_template import MarketInterface

logging.basicConfig(filename='test_market_interface.log', filemode='w', level=logging.DEBUG)
logging.getLogger().setLevel(logging.INFO)
logging.getLogger().addHandler(logging.StreamHandler())
logger = logging.getLogger("test_market_interface")


class TestMarketInterface (MarketInterface):
    def __init__(self):
        MarketInterface.__init__(self, market_interface_id="TEST_INTERFACE")
        logger.info("TEST MARKET INTERFACE INITIALIZED")

    def make_rest_request(self):
        pass

    def create_websocket_stream(self):
        pass

    def send_websocket_command(self, websocket, payload):
        pass

    def on_websocket_recv(self, msg):
        pass

    def interface_main_cycle(self):
        pass


test_interface = TestMarketInterface()
