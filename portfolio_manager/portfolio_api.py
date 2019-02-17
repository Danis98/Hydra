import threading
import socket
import logging
import json

logger = logging.getLogger('portfolio_server')

BUFFER_SIZE = 2048

# TODO: implement component identification and authentication mechanisms


class ServerThread (threading.Thread):
    """
    Main server thread for the portfolio.
    Runs in parallel with the main portfolio manager thread and handles
    incoming requests.
    """
    def __init__(self, port, strategies, market_interfaces):
        """
        Initializes the server thread with the parameters needed for operation.

        :param port: port on which it listens
        :param strategies: reference to the object containing the strategy data
        :param market_interfaces: reference to the object containing market interface data
        """
        threading.Thread.__init__(self)

        self.strategies = strategies
        self.market_interfaces = market_interfaces

        self.subscriptions = {}

        # initialize socket with queue length 5, listening on the specified port
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.sock.bind(('localhost', port))
        self.sock.listen(5)
        logger.info('Server initialized')

    def run(self):
        """
        Main server loop: accept connection, spawn a new thread handling it and continue listening.
        """
        while True:
            (client_socket, address) = self.sock.accept()
            logger.info('Accepted connection: %r' % (address,))
            handler = RequestHandler(client_socket, self.strategies, self.market_interfaces)
            handler.start()


class RequestHandler (threading.Thread):
    """
    Takes care of handling incoming requests.
    Spawned by the main server thread, it runs parallel to the other threads and exits when the request
    has been handled.

    Request is composed of:
        query: ID of the request (string)
        data: json object with request-specific data

    Response message status:
        SUCCESS : request executed successfully, may have data field
        FAIL : request could not be executed for some reason, specified in message field

    Recognized requests:
        REGISTER_STRATEGY: register new strategy with the manager
        REGISTER_MARKET_INTERFACE: register new market interface with the manager
        SUBSCRIBE: subscribe to market interface data feed
        UNSUBSCRIBE: unsubscribe from data feed
    """
    def __init__(self, client_socket, strategies, market_interfaces):
        """
        Initializes handler

        :param client_socket: socket used to communicate with the requester
        :param strategies: reference to the object containing the strategy data
        :param market_interfaces: reference to the object containing the market interface data
        """
        threading.Thread.__init__(self)

        self.socket = client_socket
        self.strategies = strategies
        self.market_interfaces = market_interfaces

    def run(self):
        """
        Main handling function, checks the kind of query and calls
        the appropriate handler function.
        If the query is not recognized, an error message is sent back.

        Handlers accept as argument the data field of the request
        """
        logger.debug('Handling request')
        request = json.loads(self.socket.recv(BUFFER_SIZE).decode())

        if request['query'] == 'REGISTER_STRATEGY':
            self.register_strategy(request['data'])
        elif request['query'] == 'REGISTER_MARKET_INTERFACE':
            self.register_market_interface(request['data'])
        elif request['query'] == 'SUBSCRIBE':
            self.subscribe(request['data'])
        elif request['query'] == 'UNSUBSCRIBE':
            self.unsubscribe(request['data'])
        else:
            logger.error('Unknown request: %s' % request['query'])
            resp = {
                'status': 'FAIL',
                'message': 'API query not defined'
            }
            self.socket.send(json.dumps(resp).encode())

    # TODO: implement exception handling when using sockets in strategy/interface registration

    def register_strategy(self, request_data):
        """
        Register a new strategy with the manager.
        Called on strategy start. An unregistered strategy will not be able to access
        other endpoints exposed by the manager.

        :param request_data: specifies the strategy parameters. It contains:
            strategy_id: unique ID of the strategy
            strategy_address: IP address of the strategy server, to which the other components will send messages
            strategy_port: port of said strategy server
        """

        strategy_id = request_data['strategy_id']
        strategy_address = request_data['strategy_address']
        strategy_port = request_data['strategy_port']

        # if strategy is already registered, a restart must have occurred,
        # so the sanest response for now is to refresh its entry
        # TODO: preserve managed assets and other permanent parameters
        if strategy_id in self.strategies:
            logger.error('Strategy %s already registered, updating...' % strategy_id)
            self.strategies[strategy_id] = {}

        # enter the initial state into the object
        self.strategies[strategy_id] = {
            'strategy_id': strategy_id,
            'address': strategy_address,
            'port': strategy_port,
            'status': 'IDLE',
            'allocated_resources': '0'
        }

        # send successful response and close connection
        logger.info("Strategy %s successfully registered" % strategy_id)
        resp = {
            'status': 'SUCCESS'
        }
        self.socket.send(json.dumps(resp).encode())
        self.socket.close()

    def register_market_interface(self, request_data):
        """
        Register a new market interface with the manager.
        Called on interface start. An unregistered interface will not be able to access
        other endpoints exposed by the manager.

        :param request_data: specifies the interface parameters. It contains:
            interface_id: unique ID of the interface
            interface_address: IP address of the interface server, to which the other components will send messages
            interface_port: port of said interface server
        """
        interface_id = request_data['market_interface_id']
        interface_address = request_data['market_interface_address']
        interface_port = request_data['market_interface_port']

        # if interface is already registered, a restart must have occurred,
        # so the sanest response for now is to refresh its entry
        # TODO: preserve active subscriptions and other permanent parameters
        if interface_id in self.market_interfaces:
            logger.error('Market interface %s already registered, updating...' % interface_id)
            self.market_interfaces[interface_id] = {}

        # enter initial information
        self.market_interfaces[interface_id] = {
            'address': interface_address,
            'port': interface_port
        }

        # send successful response and close connection
        logger.info("Market interface %s successfully registered" % interface_id)
        resp = {
            'status': 'SUCCESS'
        }
        self.socket.send(json.dumps(resp).encode())
        self.socket.close()

    # TODO: implement manager list of active subscriptions and associated interfaces

    def subscribe(self, request_data):
        """
        Subscribe the strategy to the data feed of the specified market interface.
        The strategy will receive data from the interface periodically until it unsubscribes
        from this feed.

        This function basically relays the request to one instance of the requested market interface,
        and returns the result of the query to the strategy.

        :param request_data: contains necessary data for connection between the strategy and the interface:
            strategy_id: ID identifying the subscribing strategy
            market_interface_id: ID identifying the requested market interface
            symbol: symbol on which to receive the data
            frequency: frequency of data feed
        """
        # TODO: specify frequency format
        strategy_id = request_data['strategy_id']
        market_interface_id = request_data['market_interface_id']
        symbol = request_data['symbol']
        frequency = request_data['frequency']

        # handle unknown strategy
        if strategy_id not in self.strategies:
            logger.error('Unknown strategy %s' % strategy_id)
            self.socket.send(json.dumps({
                'status': 'FAIL',
                'message': 'Unknown strategy %s' % strategy_id
            }).encode())
            self.socket.close()
            return

        # handle unknown market interface
        if market_interface_id not in self.market_interfaces:
            logger.error('Unknown market interface %s' % market_interface_id)
            self.socket.send(json.dumps({
                'status': 'FAIL',
                'message': 'Unknown market interface %s' % market_interface_id
            }).encode())
            self.socket.close()
            return

        # get addresses and ports of strategy and interface
        # TODO: implement load balancing on market interfaces
        strategy_address = self.strategies[strategy_id]['address']
        strategy_port = self.strategies[strategy_id]['port']
        interface_address = self.market_interfaces[market_interface_id]['address']
        interface_port = self.market_interfaces[market_interface_id]['port']

        # query to the interface, specifying the subscription details
        query = {
            'query': 'INTERFACE_SUBSCRIBE',
            'data': {
                'strategy_id': strategy_id,
                'strategy_address': strategy_address,
                'strategy_port': strategy_port,
                'symbol': symbol,
                'frequency': frequency
            }
        }

        # connect to the interface
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        try:
            s.connect((interface_address, interface_port))
        except ConnectionRefusedError:
            logger.error('Could not connect to market interface %s' % market_interface_id)
            self.socket.send(json.dumps({
                'status': 'FAIL',
                'message': 'Manager could not connect to market interface %s' % market_interface_id
            }).encode())
            self.socket.close()
            return

        # send query to interface and then forward response to the strategy
        try:
            s.send(json.dumps(query).encode())
            resp = json.loads(s.recv(1024).decode())

            self.socket.send(resp)
            self.socket.close()
            return
        except socket.timeout:
            logger.error('Connection timed out with interface during subscription')
            self.socket.send(json.dumps({
                'status': 'FAIL',
                'message': 'Manager connection timed out with interface during subscription'
            }).encode())
            self.socket.close()
            return

    def unsubscribe(self, request_data):
        """
        Unsubscribe from a specified subscription.
        Like the subscription handler, pretty much forwards the request to the appropriate
        interface.

        :param request_data: contains data specifying the subscription:
            sub_handle: unique handle of the subscription
        """
        sub_handle = request_data['sub_handle']
        market_interface_id = request_data['market_interface_id']

        # handle unknown market interface
        if market_interface_id not in self.market_interfaces:
            logger.error('Unknown market interface %s' % market_interface_id)
            self.socket.send(json.dumps({
                'status': 'FAIL',
                'message': 'Unknown market interface %s' % market_interface_id
            }).encode())
            self.socket.close()
            return

        # get interface address and port
        interface_address = self.market_interfaces[market_interface_id]['address']
        interface_port = self.market_interfaces[market_interface_id]['port']

        # query to interface
        query = {
            'query': 'INTERFACE_UNSUBSCRIBE',
            'data': {
                'sub_handle': sub_handle
            }
        }

        # connect to interface
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        try:
            s.connect((interface_address, interface_port))
        except ConnectionRefusedError:
            logger.error('Could not connect to market interface %s' % market_interface_id)
            self.socket.send(json.dumps({
                'status': 'FAIL',
                'message': 'Manager could not connect to market interface %s' % market_interface_id
            }).encode())
            self.socket.close()
            return

        # send query, then forward the response to the strategy
        try:
            s.send(json.dumps(query).encode())
            resp = json.loads(s.recv(1024).decode())

            self.socket.send(resp)
            self.socket.close()
            return
        except socket.timeout:
            logger.error('Connection timed out with interface during subscription')
            self.socket.send(json.dumps({
                'status': 'FAIL',
                'message': 'Manager connection timed out with interface during subscription'
            }).encode())
            self.socket.close()
            return
