import time
import logging

from common.messaging import message_to_address


def feed_callback(interface, sub_handle, resp, logger):
    if resp['status'] == 'SUCCESS':
        logger.debug("Pushed feed successfully")
    elif resp['status'] == 'FAIL':
        logger.error("Could not push feed: %s, cancelling subscription" % resp['message'])
        del interface.subscriptions[sub_handle]


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


    # push feed data periodically
    while subscription_handle in interface.subscriptions:
        # prepare data to be sent
        query = {
            'query': 'MARKET_DATA_FEED',
            'data': interface.get_data(subscription_handle)
        }

        message_to_address(strategy_address,
                           strategy_port,
                           query,
                           False,
                           lambda res: feed_callback(interface, subscription_handle, res, logger))

        time.sleep(timeout)
