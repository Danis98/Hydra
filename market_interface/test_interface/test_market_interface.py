import logging

from market_interface.market_interface_template import MarketInterface

logging.basicConfig(filename='test_market_interface.log', filemode='w', level=logging.DEBUG)
logging.getLogger().setLevel(logging.INFO)
logging.getLogger().addHandler(logging.StreamHandler())
logger = logging.getLogger("test_market_interface")


class CexioMarketInterface (MarketInterface):
    def __init__(self):
        MarketInterface.__init__(self)
        logger.info("TEST MARKET INTERFACE")


cexio_interface = CexioMarketInterface()
