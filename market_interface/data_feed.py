import socket
import logging
import json
import time


def push_feed(interface, subscription_handle):
    """
    Periodically push feed data to the subscriber.

    :param interface: parent market interface
    :param subscription_handle: handle of the served subscription
    """
    logger = logging.getLogger('data_feed_%s' % subscription_handle)

    strategy_address = interface.subscriptions[subscription_handle]['strategy_address']
    strategy_port = interface.subscriptions[subscription_handle]['strategy_port']
    timeout = interface.subscriptions[subscription_handle]['frequency']
    logger.info("Data sender initialized for subscription %s" % subscription_handle)

    # connect to the subscriber
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    try:
        s.connect((strategy_address, strategy_port))
    except ConnectionRefusedError:
        logger.error('Could not connect to strategy')
        return
    logger.debug("Connected to the subscriber")

    # push feed data periodically
    while subscription_handle in interface.subscriptions:
        # prepare data to be sent
        query = {
            'query': 'MARKET_DATA_FEED',
            'data': {
                'message': 'TEST'
            }
        }

        # send it, if the connection is ended then cancel subscription
        try:
            s.send(json.dumps(query).encode())
        except socket.timeout:
            logger.error('Connection timed out with strategy during feed push')
        except ConnectionResetError:
            logger.error('Connection reset by subscriber')
            del interface.subscriptions[subscription_handle]
            break
        except BrokenPipeError:
            logger.error('Connection failed, terminating subscription...')
            del interface.subscriptions[subscription_handle]
            break
        else:
            logger.debug("Push successful")
        time.sleep(timeout)
