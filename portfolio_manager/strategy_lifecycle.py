import json
import socket
import logging


"""
Helper functions to handle lifecycle signals to strategies, used by manager.
"""

logger = logging.getLogger('portfolio_manager')


def init(address, port, resources):
    """
    Send initialization signal, strategy should start initializing phase.
    :param address: address to send the signal to
    :param port: associated port
    :param resources: amount of initial resources assigned to the strategy
    :return: True/False based on whether the message was sent successfully
    """
    request = {
        'query': 'INIT',
        'data': {
            'resources': resources
        }
    }
    # connect to strategy
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    try:
        sock.connect((address, port))
    except ConnectionRefusedError:
        logger.error('Could not initialize with strategy, could not connect to it')
        return False
    # send command
    try:
        sock.send(json.dumps(request).encode())
    except socket.timeout:
        logger.error('Could not initialize with strategy, connection timed out')
        return False

    logger.info("Initialization command sent")
    return True


# TODO implement other lifecycle commands in manager

def start():
    pass


def stop():
    pass
