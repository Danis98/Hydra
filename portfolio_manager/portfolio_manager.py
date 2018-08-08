import json
import time
import _thread
import logging

from portfolio_api import start_server

logging.basicConfig(filename='portfolio_manager.log', filemode='w', level=logging.DEBUG)
logger = logging.getLogger('portfolio_manager')

logger.info('Starting portfolio manager...')

# read config file
config = json.loads(open("config.json", "r").read())

logger.debug('Config loaded')

PORT = config['port']
REFRESH_TIMEOUT = config['refresh_timeout']

# registered strategies
strategies = []
# registered data managers, usually one, more for load balancing
data_managers = []

# set to true to kill main process
stop_manager = False

try:
    _thread.start_new_thread(start_server, (PORT, strategies, data_managers))
except:
    logger.error('Could not start server')
    exit(1)

logger.debug('Setup complete, starting main cycle...')

# main process cycle
while not stop_manager:
    for strategy in strategies:
        print(strategy['name'])

    time.sleep(REFRESH_TIMEOUT)
