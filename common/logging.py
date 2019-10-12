import logging


def setup_logger(fname):
    logging.basicConfig(filename=fname, filemode='w', level=logging.DEBUG)
    handler = logging.StreamHandler()
    handler.setLevel(logging.INFO)
    logging.getLogger().addHandler(handler)
