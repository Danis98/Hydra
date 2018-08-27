import sys
import json
import socket
import logging
import threading


class StrategyServer (threading.Thread):

    logger = logging.getLogger('strategy_server')

    def __init__(self, port, strategy):
        threading.Thread.__init__(self)

        self.PORT = port
        self.STRATEGY = strategy
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.socket.bind(('localhost', self.PORT))
        self.socket.listen(5)

        self.logger.info('Strategy server started successfully')

    def run(self):
        while True:
            (src_socket, port) = self.socket.accept()
            handler = threading.Thread(target=self.handle_request, args=(src_socket,))
            handler.start()

    def handle_request(self, src_socket):
        msg = json.loads(src_socket.recv(1024).decode())
        self.logger.debug("Received message: %r" % json.dumps(msg))
        # handle incoming messages
        if msg['query'] == 'INIT':
            # connect market manager and run user-defined init
            if 'market_manager_address' in msg['params'] and 'market_manager_port' in msg['params']:
                self.STRATEGY.connect_market_manager(msg['params']['market_manager_address'], msg['params']['market_manager_port'])
            self.STRATEGY.on_init(msg['params'])
        elif msg['query'] == 'START':
            self.STRATEGY.on_start(msg['params'])
        elif msg['query'] == 'PAUSE':
            self.STRATEGY.on_pause(msg['params'])
        elif msg['query'] == 'RESUME':
            self.STRATEGY.on_resume(msg['params'])
        elif msg['query'] == 'STOP':
            self.STRATEGY.on_stop(msg['params'])


class Strategy:
    def __init__(self, strategy_name, mode):
        logger = logging.getLogger('strategy_framework')

        # load initial config
        self.config = json.loads(open('config.json', 'r').read())

        self.STRATEGY_NAME = strategy_name
        self.MODE = mode
        self.PORT = self.config['port']
        self.MANAGER_ADDRESS = self.config['manager_address']
        self.MANAGER_PORT = self.config['manager_port']
        self.MARKET_MANAGER_CONNECTED = False
        self.MARKET_MANAGER_ADDRESS = self.config['market_manager_address'] if 'market_manager_address' in self.config else ''
        self.MARKET_MANAGER_PORT = self.config['market_manager_port'] if 'market_manager_port' in self.config else ''
        self.STATUS = 'IDLE'

        self.market_socket = None

        # register strategy
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        try:
            s.connect((self.MANAGER_ADDRESS, self.MANAGER_PORT))
        except ConnectionRefusedError:
            logger.error('Could not connect to manager')
            sys.exit()

        query = {
            'query': 'REGISTER_STRATEGY',
            'data': {
                'strategy_name': self.STRATEGY_NAME,
                'strategy_address': 'localhost',
                'strategy_port': self.PORT,
                'mode': self.MODE,
                'send_market_manager': 'market_manager_address' not in self.config or 'market_manager_port' not in self.config
            }
        }
        try:
            s.send(json.dumps(query).encode())
            resp = json.loads(s.recv(1024).decode())

            if resp['status'] == 'FAIL':
                logger.error('Could not register strategy: %s', resp['message'])
                sys.exit()
            elif resp['status'] == 'SUCCESS':
                logger.info('Strategy registered')
        except socket.timeout:
            logger.error('Connection timed out with manager during registration')
            sys.exit()

        # start listening server
        strategy_server = StrategyServer(self.PORT, self)
        strategy_server.start()

        # start main strategy
        self.strategy_cycle()

    # handle connection to market manager
    def connect_market_manager(self, address, port):
        self.market_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        #TODO connect to market manager

    # main strategy body, to implement in actual strategy
    def strategy_cycle(self):
        pass

    # lifecycle funcs, to implement by strategy

    def on_init(self, params):
        pass

    def on_start(self, params):
        pass

    def on_pause(self, params):
        pass

    def on_resume(self, params):
        pass

    def on_stop(self, params):
        pass

    # event handlers, to implement by strategy

    def on_funds_reallocation(self, params):
        pass
