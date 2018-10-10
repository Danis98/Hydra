import threading
import socket
import logging
import json

logger = logging.getLogger('portfolio_server')

BUFFER_SIZE = 2048


# Class handling incoming requests to the portfolio manager
class RequestHandler (threading.Thread):
    def __init__(self, client_socket, strategies, market_interfaces):
        threading.Thread.__init__(self)

        self.socket = client_socket
        self.strategies = strategies
        self.market_interfaces = market_interfaces

    def run(self):
        logger.debug('Handling request')
        request = json.loads(self.socket.recv(BUFFER_SIZE).decode())
        if request['query'] == 'REGISTER_STRATEGY':
            self.register_strategy(request['data'])
        elif request['query'] == 'REGISTER_MARKET_INTERFACE':
            self.register_market_interface(request['data'])
        else:
            logger.error('Unknown request: %s' % request['query'])
            resp = {
                'status': 'FAIL',
                'message': 'API query not defined'
            }
            self.socket.send(json.dumps(resp).encode())

    # REGISTER_STRATEGY handler
    def register_strategy(self, request_data):
        strategy_id = request_data['strategy_id']
        strategy_address = request_data['strategy_address']
        strategy_port = request_data['strategy_port']
        # if strategy is already registered, reject the request
        if strategy_id in self.strategies:
            logger.error('Strategy %s already registered, updating...' % strategy_id)
            self.strategies[strategy_id] = {}
        # register the strategy
        self.strategies[strategy_id] = {
            'strategy_id': strategy_id,
            'strategy_address': strategy_address,
            'strategy_port': strategy_port,
            'status': 'IDLE',
            'allocated_resources': '0'
        }
        # send successful response
        logger.info("Strategy %s successfully registered" % strategy_id)
        resp = {
            'status': 'SUCCESS'
        }
        self.socket.send(json.dumps(resp).encode())
        self.socket.close()

    # REGISTER_MARKET_INTERFACE handler
    def register_market_interface(self, request_data):
        interface_id = request_data['market_interface_id']
        interface_address = request_data['market_interface_address']
        interface_port = request_data['market_interface_port']

        # if interface is already registered, reject the request
        if interface_id in self.market_interfaces:
            logger.error('Market interface %s already registered, updating...' % interface_id)
            self.market_interfaces[interface_id] = {}

        self.market_interfaces[interface_id] = {
            'address': interface_address,
            'port': interface_port
        }
        # send successful response
        logger.info("Market interface %s successfully registered" % interface_id)
        resp = {
            'status': 'SUCCESS'
        }
        self.socket.send(json.dumps(resp).encode())
        self.socket.close()


class ServerThread (threading.Thread):
    def __init__(self, port, strategies, market_interfaces):
        threading.Thread.__init__(self)

        self.strategies = strategies
        self.market_interfaces = market_interfaces

        # initialize socket with queue length 5
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.sock.bind(('localhost', port))
        self.sock.listen(5)
        logger.info('Server initialized')

    def run(self):
        while True:
            (client_socket, address) = self.sock.accept()
            logger.info('Accepted connection: %r' % (address,))
            handler = RequestHandler(client_socket, self.strategies, self.market_interfaces)
            handler.start()
