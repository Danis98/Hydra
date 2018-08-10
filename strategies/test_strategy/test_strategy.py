import socket
import json
import logging

logging.basicConfig(filename='test_strategy.log', filemode='w', level=logging.DEBUG)
logger = logging.getLogger('test_strategy')

logger.info('Starting test strategy...')

config = json.loads(open('config.json', 'r').read())

PORT = config['port']
MANAGER_ADDRESS = config['manager_address']
MANAGER_PORT = config['manager_port']

print(MANAGER_ADDRESS)
print(MANAGER_PORT)

s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
s.connect((MANAGER_ADDRESS, MANAGER_PORT))

query = {
    'query': 'REGISTER_STRATEGY',
    'data': {
        'strategy_name': 'Test strategy',
        'strategy_address': 'localhost',
        'strategy_port': PORT,
        'send_data_manager': True
    }
}

s.send(json.dumps(query).encode())
print(s.recv(1024).decode())
