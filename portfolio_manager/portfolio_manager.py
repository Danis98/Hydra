import json
import time
import logging

# noinspection PyUnresolvedReferences
from portfolio_api import ServerThread
# noinspection PyUnresolvedReferences
from strategy_lifecycle import init, start, pause, resume, stop

logging.basicConfig(filename='portfolio_manager.log', filemode='w', level=logging.DEBUG)
logging.getLogger().setLevel(logging.INFO)
logging.getLogger().addHandler(logging.StreamHandler())
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
market_managers = []

# set to true to kill main process
stop_manager = False

try:
    logger.debug('Starting server...')
    portfolio_server = ServerThread(PORT, strategies, market_managers)
    portfolio_server.start()
except Exception as e:
    logger.error('Could not start server')
    print(e)
    exit(1)

logger.info('Setup complete, starting main cycle...')

TEST_MONEY_AMOUNT = 1000

# main process cycle
while not stop_manager:
    for strategy in strategies:
        # do actions based on strategy status
        if strategy['status'] == 'IDLE':
            # initialize strategy with test amount of money
            strategy['allocated_resources'] = TEST_MONEY_AMOUNT
            if init(address=strategy['strategy_address'],
                    port=strategy['strategy_port'],
                    resources=strategy['allocated_resources']):
                strategy['status'] = 'INITIALIZING'
        elif strategy['status'] == 'INITIALIZING':
            # TODO define behavior if strategy is initializing
            pass
        elif strategy['status'] == 'PAUSED':
            # TODO define behavior if strategy is paused
            pass
        elif strategy['running'] == 'RUNNING':
            # TODO define behavior if strategy is running
            pass

    time.sleep(REFRESH_TIMEOUT)
