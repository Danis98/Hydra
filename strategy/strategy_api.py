import logging
import threading
import socket
import json


class StrategyApiServer (threading.Thread):
    """
    Main server thread for the strategy.
    Runs in parallel with the main strategy thread and handles
    incoming requests.
    """
    def __init__(self, host, port, strategy):
        """
        Initializes server, then starts listening for incoming connections.

        :param host: address of the server
        :param port: port of the server
        :param strategy: reference to the parent strategy, used to access its data
        """
        threading.Thread.__init__(self)

        self.logger = logging.getLogger('strategy_server')

        self.HOST = host
        self.PORT = port
        self.STRATEGY = strategy

        # create socket and start listening
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.socket.bind((self.HOST, self.PORT))
        self.socket.listen(5)

        self.logger.info('Strategy server started successfully')

    def run(self):
        """Accept connections and handle them in a separate child thread"""
        while True:
            (src_socket, port) = self.socket.accept()
            handler = threading.Thread(target=self.handle_request, args=(src_socket,))
            handler.start()

    def handle_request(self, src_socket):
        """
        Route execution to the appropriate handler implemented by the strategy.

        :param src_socket: socket used by the incoming request
        """
        # read request
        msg = json.loads(src_socket.recv(1024).decode())
        self.logger.debug("Received message: %r" % json.dumps(msg))

        # lock thread to avoid race conditions
        lock = threading.Lock()
        lock.acquire()

        # call appropriate handler function
        if msg['query'] == 'INIT':
            self.STRATEGY.on_init(msg['data'])
        elif msg['query'] == 'START':
            self.STRATEGY.on_start(msg['data'])
        elif msg['query'] == 'RESUME':
            self.STRATEGY.on_resume(msg['data'])
        elif msg['query'] == 'STOP':
            self.STRATEGY.on_stop(msg['data'])
        elif msg['query'] == 'REALLOCATE':
            self.STRATEGY.on_funds_reallocation(msg['data'])
            # TODO reallocation done message
        else:
            self.logger.error('Unknown request: %s' % msg['query'])

        # query executed, release lock and close connection
        lock.release()
        src_socket.close()
