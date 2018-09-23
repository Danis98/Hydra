import socket
import json
import logging


logger = logging.getLogger('portfolio_manager')


def init(address, port, resources):
    # connect to strategy
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    try:
        sock.connect((address, port))
        request = {
            'query': 'INIT',
            'params': {
                'resources': resources
            }
        }
        sock.send(json.dumps(request).encode())
    except socket.timeout:
        logger.error('Could not initialize with strategy, connection timed out')
        return False
    return True


# TODO implement lifecycle commands in manager

def start():
    pass


def pause():
    pass


def resume():
    pass


def stop():
    pass
