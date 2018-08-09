import json
import time
import threading
import logging

from portfolio_api import ServerThread

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
    logger.debug('Starting server...')
    portfolio_server = ServerThread(PORT, strategies, data_managers)
    portfolio_server.run()
except Exception as e:
    logger.error('Could not start server')
    print(e)
    exit(1)

logger.debug('Setup complete, starting main cycle...')

# main process cycle
while not stop_manager:
    for strategy in strategies:
        print(strategy['name'])

    time.sleep(REFRESH_TIMEOUT)
