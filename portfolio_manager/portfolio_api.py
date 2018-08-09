import threading
import socket
import logging

logger = logging.getLogger('portfolio_server')


class RequestHandler (threading.Thread):
    def __init__(self, client_socket, strategies, data_managers):
        threading.Thread.__init__(self)

        self.socket = client_socket
        self.strategies = strategies
        self.data_managers = data_managers

    def run(self):
        logger.debug('Handling request')
        pass


class ServerThread (threading.Thread):
    def __init__(self, port, strategies, data_managers):
        threading.Thread.__init__(self)

        self.strategies = strategies
        self.data_managers = data_managers

        # initialize socket with queue length 5
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.sock.bind((socket.gethostname(), port))
        self.sock.listen(5)
        logger.info('Server initialized')

    def run(self):
        while True:
            (client_socket, address) = self.sock.accept()
            logger.info('Accepted connection: %r', address)
            handler = RequestHandler(client_socket, self.strategies, self.data_managers)
            handler.run()
