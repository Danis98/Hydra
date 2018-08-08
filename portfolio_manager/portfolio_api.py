import socket
import logging

logger = logging.getLogger('portfolio_server')

def start_server(port, strategies, data_managers):
    logger.debug('Starting server...')

    # initialize socket with queue length 5
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.bind((socket.gethostname(), port))
    sock.listen(5)
    logger.debug('Socket initialized')

    while True:
        (client_socket, address) = sock.accept()
        logger.info('Accepted connection: %r', address)
