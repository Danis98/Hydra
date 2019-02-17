import threading
import logging
import json
import string
import random
import socket

# noinspection PyUnresolvedReferences
from market_interface.data_feed import push_feed

logger = logging.getLogger('interface_api')


class MarketInterfaceRequestHandler (threading.Thread):
    """
    Handles the assigned incoming request, then exits.
    Runs in its own thread.
    """
    def __init__(self, client_socket, interface):
        """
        Initialize handler.

        :param client_socket: socket used for communication with the requester (usually the manager)
        :param interface: reference to the parent market interface
        """
        threading.Thread.__init__(self)

        self.socket = client_socket
        self.interface = interface

    def run(self):
        """
        Read the request, decide which handler to use, and call it.
        If a query is not recognized, a FAIL is sent back.

        Implemented handlers:
            INTERFACE_SUBSCRIBE: subscribe to a data feed
        """
        # TODO: implement unsubscription, bulk data request, order handling
        logger.debug('Handling request')

        # read request
        request = json.loads(self.socket.recv(self.interface.BUFFER_SIZE).decode())

        # decide which handler function to call
        if request['query'] == 'INTERFACE_SUBSCRIBE':
            self.handle_subscription(request['data'])
        else:
            logger.error('Unknown request: %s' % request['query'])
            resp = {
                'status': 'FAIL',
                'message': 'API query not defined'
            }
            # TODO: better error handling here
            try:
                self.socket.send(json.dumps(resp).encode())
            except socket.error:
                logger.error("Error while sending FAIL message")

    def handle_subscription(self, req_data):
        """
        Subscribe strategy to a data feed, sent with the requested frequency.

        Generates a unique subscription handle, inserts the corresponding entry into the interface,
        and starts the data sender tasked with periodically sending feed data.

        :param req_data: contains the data regarding the request:
            strategy_id: ID of the requesting strategy
            strategy_address: address of the strategy server socket
            strategy_port: port of te strategy server socket
            symbol: requested symbol
            frequency: time elapsed between feed messages, in seconds
        """
        # TODO: implement data granularity
        logger.info("Subscription request received from %s" % req_data['strategy_id'])

        # generate handle
        rand_str = ''.join(random.choices(string.ascii_letters + string.digits, k=16))
        sub_handle = "%s_%s_%s:%s" % (self.interface.INTERFACE_ID,
                                      req_data['symbol'],
                                      req_data['strategy_id'],
                                      rand_str)

        # initialize data sender
        data_sender = threading.Thread(target=push_feed,
                                       args=(self.interface, sub_handle,))

        # insert subscription entry
        self.interface.subscriptions[sub_handle] = {
            'strategy_address': req_data['strategy_address'],
            'strategy_port': req_data['strategy_port'],
            'symbol': req_data['symbol'],
            'frequency': req_data['frequency'],
            'sender': data_sender
        }

        # start data sender
        data_sender.start()

    def handle_unsubscription(self, req_data):
        pass

    def handle_bulk_data_request(self, req_data):
        pass

    def handle_order(self, req_data):
        pass


class MarketInterfaceServer (threading.Thread):
    """
    Server for incoming requests to the market interface.
    Listens on the specified port, and spawns a request handler in a
    separate thread to handle incoming requests.
    """
    def __init__(self, host, port, interface):
        """
        Initialize the server.

        :param host: address of the server
        :param port: port of the server
        :param interface: reference to the parent interface, used to modify data in it
        """
        threading.Thread.__init__(self)
        self.HOST = host
        self.PORT = port
        self.interface = interface

        # initialize listening socket
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.socket.bind((self.HOST, self.PORT))
        self.socket.listen(5)

        logger.info('Interface server started successfully')

    def run(self):
        """
        Listen for incoming requests and handle them in a separate thread
        """
        while True:
            (client_socket, address) = self.socket.accept()
            logger.info('Accepted connection: %r' % (address,))
            handler = MarketInterfaceRequestHandler(client_socket, self.interface)
            handler.start()
