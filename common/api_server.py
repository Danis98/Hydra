import abc
import socket
import logging
import threading


MAX_CONNECTION_QUEUE_LEN = 5


class ApiServer(threading.Thread):
    """
    Server for incoming requests to the specified address.
    Listens on the specified port, and spawns a request handler in a
    separate thread to handle incoming requests.
    """

    __metaclass__ = abc.ABCMeta

    def __init__(self, host, port):
        """
        Generic API server used by the various components of the system to receive and
        handle incoming queries

        :param host: address of the server
        :param port: port of the server
        """
        threading.Thread.__init__(self)

        self.logger = logging.getLogger('api_server')

        self.HOST = host
        self.PORT = port

        # create socket and start listening
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.socket.bind((self.HOST, self.PORT))
        self.socket.listen(MAX_CONNECTION_QUEUE_LEN)

    def run(self):
        """
        Listen for incoming requests and handle them in a separate thread
        """
        while True:
            (client_socket, address) = self.socket.accept()
            self.logger.info('Accepted connection: %r' % (address,))
            handler = self.get_handler(client_socket)
            handler.start()

    @abc.abstractmethod
    def get_handler(self, client_socket):
        """
        Provide request handler to use on incoming requests.
        Abstract method, MUST be implemented by individual API servers.

        :param client_socket: incoming request socket
        :return: a subclass of RequestHandler
        """
