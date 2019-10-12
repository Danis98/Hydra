import string
import random
import logging
import threading

from market_interface.data_feed import push_feed
from common.request_handler import RequestHandler


class MarketInterfaceRequestHandler (RequestHandler):
    def __init__(self, client_socket, interface):
        """
        Initialize handler.

        :param client_socket: socket used for communication with the requester (usually the manager)
        :param interface: reference to the parent market interface
        """
        super().__init__(client_socket)
        self.logger = logging.getLogger('interface_request_handler')

        self.INTERFACE = interface

        self.query_handlers = {
            'INTERFACE_SUBSCRIBE': self.subscribe,
            'INTERFACE_UNSUBSCRIBE': self.unsubscribe,
            'BULK_DATA': self.bulk_data_request,
            'ORDER': self.order
        }

    def subscribe(self, req_data):
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
        self.logger.info("Subscription request received from %s" % req_data['strategy_id'])

        # generate handle
        rand_str = ''.join(random.choices(string.ascii_letters + string.digits, k=16))
        sub_handle = "%s_%s_%s:%s" % (self.INTERFACE.INTERFACE_ID,
                                      req_data['symbol'],
                                      req_data['strategy_id'],
                                      rand_str)

        # initialize data sender
        data_sender = threading.Thread(target=push_feed,
                                       args=(self.INTERFACE, sub_handle,))

        # insert subscription entry
        self.INTERFACE.subscriptions[sub_handle] = {
            'strategy_address': req_data['strategy_address'],
            'strategy_port': req_data['strategy_port'],
            'symbol': req_data['symbol'],
            'frequency': req_data['frequency'],
            'sender': data_sender
        }

        # start data sender
        data_sender.start()

        return {
            'status': 'SUCCESS',
            'data': {
                'subscription_handle': sub_handle
            }
        }

    def unsubscribe(self, req_data):
        pass

    def bulk_data_request(self, req_data):
        pass

    def order(self, req_data):
        pass
