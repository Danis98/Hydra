import threading
import socket
import logging
import json

logger = logging.getLogger('portfolio_server')

BUFFER_SIZE = 1024
strategy_names = []


class RequestHandler (threading.Thread):
    def __init__(self, client_socket, strategies, market_managers):
        threading.Thread.__init__(self)

        self.socket = client_socket
        self.strategies = strategies
        self.market_managers = market_managers

    def run(self):
        logger.debug('Handling request')
        request = json.loads(self.socket.recv(BUFFER_SIZE).decode())
        if request['query'] == 'REGISTER_STRATEGY':
            self.register_strategy(request['data'])
        elif request['query'] == 'GET_MARKET_MANAGER':
            self.get_market_manager(request['data'])
        else:
            logger.error('Unknown request: %s' % request['query'])

    # REGISTER_STRATEGY handler
    def register_strategy(self, request_data):
        strategy_name = request_data['strategy_name']
        strategy_address = request_data['strategy_address']
        strategy_port = request_data['strategy_port']
        # if strategy is already registered, reject the request
        if strategy_name in strategy_names:
            logger.error('Strategy %s already registered' % strategy_name)
            resp = {
                'status': 'FAIL',
                'message': ('Strategy %s already registered' % strategy_name)
            }
            self.socket.send(json.dumps(resp).encode())
            return
        # register the strategy
        strategy_names.append(strategy_name)
        self.strategies.append({
            'strategy_name': strategy_name,
            'strategy_address': strategy_address,
            'strategy_port': strategy_port,
            'status': 'IDLE',
            'allocated_resources': '0'
        })
        resp = {
            'status': 'SUCCESS'
        }
        self.socket.send(json.dumps(resp).encode())
        self.socket.close()

    # GET_MARKET_MANAGER handler
    def get_market_manager(self, request_data):
        manager_id = request_data['market_manager_id']
        if manager_id not in self.market_managers:
            resp = {
                'status': 'FAIL',
                'message': 'Market manager %s not found' % manager_id
            }
        else:
            resp = {
                'status': 'SUCCESS',
                'data': {
                    'market_manager_address': self.market_managers[manager_id]['address'],
                    'market_manager_port': self.market_managers[manager_id]['port']
                }
            }
        self.socket.send(json.dumps(resp).encode())
        self.socket.close()

    # REGISTER_MARKET_MANAGER handler
    def register_market_manager(self, request_data):
        manager_id = request_data['market_manager_id']
        manager_address = request_data['market_manager_address']
        manager_port = request_data['market_manager_port']

        self.market_managers[manager_id] = {
            'address': manager_address,
            'port': manager_port
        }


class ServerThread (threading.Thread):
    def __init__(self, port, strategies, market_managers):
        threading.Thread.__init__(self)

        self.strategies = strategies
        self.market_managers = market_managers

        # initialize socket with queue length 5
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.sock.bind(('localhost', port))
        self.sock.listen(5)
        logger.info('Server initialized')

    def run(self):
        while True:
            (client_socket, address) = self.sock.accept()
            logger.info('Accepted connection: %r' % (address,))
            handler = RequestHandler(client_socket, self.strategies, self.market_managers)
            handler.start()
