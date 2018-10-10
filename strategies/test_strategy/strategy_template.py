import sys
import json
import socket
import logging
import threading


# class implementing the strategy server, handles incoming messages from the other modules
# of the system, especially commands from the portfolio manager
class StrategyServer (threading.Thread):

    logger = logging.getLogger('strategy_server')

    # set up local variable, initialize socket and start listening
    def __init__(self, host, port, strategy):
        threading.Thread.__init__(self)

        self.HOST = host
        self.PORT = port
        self.STRATEGY = strategy
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.socket.bind((self.HOST, self.PORT))
        self.socket.listen(5)

        self.logger.info('Strategy server started successfully')

    # accept connections and handle them in their own thread
    def run(self):
        while True:
            (src_socket, port) = self.socket.accept()
            handler = threading.Thread(target=self.handle_request, args=(src_socket,))
            handler.start()

    # route execution to the appropriate handler implemented by the strategy
    def handle_request(self, src_socket):
        msg = json.loads(src_socket.recv(1024).decode())
        self.logger.debug("Received message: %r" % json.dumps(msg))
        if msg['query'] == 'INIT':
            self.STRATEGY.on_init(msg['params'])
        elif msg['query'] == 'START':
            self.STRATEGY.on_start(msg['params'])
        elif msg['query'] == 'RESUME':
            self.STRATEGY.on_resume(msg['params'])
        elif msg['query'] == 'STOP':
            self.STRATEGY.on_stop(msg['params'])

    # subscribe to market interface data feed
    def send_subscription(self, manager_address, manager_port, query):
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        try:
            s.connect((manager_address, manager_port))
        except ConnectionRefusedError:
            self.logger.error('Could not connect to manager')
            return

        try:
            s.send(json.dumps(query).encode())
            resp = json.loads(s.recv(1024).decode())

            if resp['status'] == 'FAIL':
                self.logger.error('Could not subscribe to data feed: %s', resp['message'])
                return None
            elif resp['status'] == 'SUCCESS':
                self.logger.info('Subscribed to data feed successfully')
                self.STRATEGY.subscriptions.append(resp['data']['subscription_handle'])

        except socket.timeout:
            self.logger.error('Connection timed out with manager during subscription')


# class implementing the basic framework of a strategy, handles interaction with the other
# components, and provides an access to data
class Strategy:
    def __init__(self, strategy_id, mode):
        self.logger = logging.getLogger('strategy_framework')

        self.RUN = True

        # load initial config
        self.config = json.loads(open('config.json', 'r').read())

        self.STRATEGY_ID = strategy_id
        self.MODE = mode
        self.STATUS = 'IDLE'
        self.HOST = self.config['host']
        self.PORT = self.config['port']
        self.allocated_funds = 0

        self.MANAGER_ADDRESS = self.config['manager_address']
        self.MANAGER_PORT = self.config['manager_port']

        self.MARKET_INTERFACES = []

        self.subscriptions = []

        # register strategy
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        try:
            s.connect((self.MANAGER_ADDRESS, self.MANAGER_PORT))
        except ConnectionRefusedError:
            self.logger.error('Could not connect to manager')
            sys.exit()

        query = {
            'query': 'REGISTER_STRATEGY',
            'data': {
                'strategy_id': self.STRATEGY_ID,
                'strategy_address': self.HOST,
                'strategy_port': self.PORT,
                'mode': self.MODE,
            }
        }
        try:
            s.send(json.dumps(query).encode())
            resp = json.loads(s.recv(1024).decode())

            if resp['status'] == 'FAIL':
                self.logger.error('Could not register strategy: %s', resp['message'])
                sys.exit()
            elif resp['status'] == 'SUCCESS':
                self.logger.info('Strategy registered')
        except socket.timeout:
            self.logger.error('Connection timed out with manager during registration')
            sys.exit()

        # start listening server
        self.strategy_server = StrategyServer(self.HOST, self.PORT, self)
        self.strategy_server.start()

        # start main strategy
        self.strategy_cycle()

    ##################################
    #        MARKET INTERFACE        #
    ##################################

    def subscribe(self, market_interface_id, symbol, frequency):
        self.logger.info("Subscribing to %s:%s..." % (market_interface_id, symbol))
        query = {
            'query': 'SUBSCRIBE',
            'data': {
                'strategy_id': self.STRATEGY_ID,
                'market_interface_id': market_interface_id,
                'symbol': symbol,
                'frequency': frequency
            }
        }

        handler = threading.Thread(target=self.strategy_server.send_subscription, args=(self.MANAGER_ADDRESS, self.MANAGER_PORT, query))
        handler.start()


    def unsubscribe(self, subscription_handle):
        pass

    def get_bulk_data(self, market_interface_id, symbol, start_time, end_time, frequency):
        pass

    def get_current_data(self, market_interface_id, symbol):
        pass

    ##################################
    #        STRATEGY METHODS        #
    ##################################

    # main strategy body, to implement in actual strategy
    def strategy_cycle(self):
        pass

    # lifecycle funcs, to implement by strategy

    def on_init(self, params):
        pass

    def on_start(self, params):
        pass

    def on_resume(self, params):
        pass

    def on_stop(self, params):
        pass

    # event handlers, to implement by strategy

    def on_funds_reallocation(self, params):
        pass
