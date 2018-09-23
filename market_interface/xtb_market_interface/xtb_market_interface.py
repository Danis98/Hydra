import logging

logging.basicConfig(filename='xtb_market_interface.log', filemode='w', level=logging.DEBUG)
logging.getLogger().setLevel(logging.INFO)
logging.getLogger().addHandler(logging.StreamHandler())