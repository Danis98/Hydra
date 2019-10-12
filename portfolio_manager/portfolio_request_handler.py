import logging

from common.messaging import message_to_address
from common.request_handler import RequestHandler


class PortfolioRequestHandler (RequestHandler):
    """
    Takes care of handling incoming requests.
    Spawned by the main server thread, it runs parallel to the other threads and exits when the request
    has been handled.

    Recognized requests:
        REGISTER_STRATEGY: register new strategy with the manager
        REGISTER_MARKET_INTERFACE: register new market interface with the manager
        SUBSCRIBE: subscribe to market interface data feed
        UNSUBSCRIBE: unsubscribe from data feed
    """
    def __init__(self, client_socket, portfolio_manager):
        """
        Initializes handler

        :param client_socket: socket used to communicate with the requester
        :param portfolio_manager: parent portfolio manager, containing the data concerning
                                strategies and interfaces
        """
        super().__init__(client_socket)
        self.logger = logging.getLogger('manager_request_handler')

        self.MANAGER = portfolio_manager

        self.query_handlers = {
            'REGISTER_STRATEGY': self.register_strategy,
            'REGISTER_MARKET_INTERFACE': self.register_market_interface,
            'INTERFACE_SUBSCRIBE': self.subscribe,
            'INTERFACE_UNSUBSCRIBE': self.unsubscribe
        }

    def register_strategy(self, request_data):
        """
        Register a new strategy with the manager.
        Called on strategy start. An unregistered strategy will not be able to access
        other endpoints exposed by the manager.

        :param request_data: specifies the strategy parameters. It contains:
            strategy_id: unique ID of the strategy
            strategy_address: IP address of the strategy server, to which the other components will send messages
            strategy_port: port of said strategy server
        """

        strategy_id = request_data['strategy_id']
        strategy_address = request_data['strategy_address']
        strategy_port = request_data['strategy_port']

        # if strategy is already registered, a restart must have occurred,
        # so the sanest response for now is to refresh its entry
        # TODO: preserve managed assets and other permanent parameters
        if strategy_id in self.MANAGER.strategies:
            self.logger.error('Strategy %s already registered, updating...' % strategy_id)
            self.MANAGER.strategies[strategy_id] = {}

        # enter the initial state into the object
        self.MANAGER.strategies[strategy_id] = {
            'strategy_id': strategy_id,
            'address': strategy_address,
            'port': strategy_port,
            'status': 'IDLE',
            'allocated_resources': '0'
        }

        # send successful response and close connection
        self.logger.info("Strategy %s successfully registered" % strategy_id)
        resp = {
            'status': 'SUCCESS',
            'data': {}
        }
        return resp

    def register_market_interface(self, request_data):
        """
        Register a new market interface with the manager.
        Called on interface start. An unregistered interface will not be able to access
        other endpoints exposed by the manager.

        :param request_data: specifies the interface parameters. It contains:
            interface_id: unique ID of the interface
            interface_address: IP address of the interface server, to which the other components will send messages
            interface_port: port of said interface server
        """
        interface_id = request_data['market_interface_id']
        interface_address = request_data['market_interface_address']
        interface_port = request_data['market_interface_port']

        # if interface is already registered, a restart must have occurred,
        # so the sanest response for now is to refresh its entry
        # TODO: preserve active subscriptions and other permanent parameters
        if interface_id in self.MANAGER.market_interfaces:
            self.logger.error('Market interface %s already registered, updating...' % interface_id)
            self.MANAGER.market_interfaces[interface_id] = {}

        # enter initial information
        self.MANAGER.market_interfaces[interface_id] = {
            'address': interface_address,
            'port': interface_port
        }

        # send successful response and close connection
        self.logger.info("Market interface %s successfully registered" % interface_id)
        resp = {
            'status': 'SUCCESS',
            'data': {}
        }
        return resp

    # TODO: implement manager list of active subscriptions and associated interfaces
    def subscribe_callback(self, response, res):
        response['status'] = res['status']
        if response['status'] == 'SUCCESS':
            self.logger.debug('Subscription made successfully!')
            response['data'] = res['data']
        elif response['status'] == 'FAIL':
            self.logger.error('Error during subscription: %s' % res['message'])
            response['message'] = res['message']
        else:
            self.logger.error('Invalid status in INTERFACE_SUBSCRIBE response: %s' % res['status'])

    def subscribe(self, request_data):
        """
        Subscribe the strategy to the data feed of the specified market interface.
        The strategy will receive data from the interface periodically until it unsubscribes
        from this feed.

        This function basically relays the request to one instance of the requested market interface,
        and returns the result of the query to the strategy.

        :param request_data: contains necessary data for connection between the strategy and the interface:
            strategy_id: ID identifying the subscribing strategy
            market_interface_id: ID identifying the requested market interface
            symbol: symbol on which to receive the data
            frequency: frequency of data feed
        """
        # TODO: specify frequency format
        strategy_id = request_data['strategy_id']
        market_interface_id = request_data['market_interface_id']
        symbol = request_data['symbol']
        frequency = request_data['frequency']

        # handle unknown strategy
        if strategy_id not in self.MANAGER.strategies:
            self.logger.error('Unknown strategy %s' % strategy_id)
            return {
                'status': 'FAIL',
                'message': 'Unknown strategy %s' % strategy_id
            }

        # handle unknown market interface
        if market_interface_id not in self.MANAGER.market_interfaces:
            self.logger.error('Unknown market interface %s' % market_interface_id)
            return {
                'status': 'FAIL',
                'message': 'Unknown market interface %s' % market_interface_id
            }

        # get addresses and ports of strategy and interface
        # TODO: implement load balancing on market interfaces
        strategy_address = self.MANAGER.strategies[strategy_id]['address']
        strategy_port = self.MANAGER.strategies[strategy_id]['port']
        interface_address = self.MANAGER.market_interfaces[market_interface_id]['address']
        interface_port = self.MANAGER.market_interfaces[market_interface_id]['port']

        # query to the interface, specifying the subscription details
        query = {
            'query': 'INTERFACE_SUBSCRIBE',
            'data': {
                'strategy_id': strategy_id,
                'strategy_address': strategy_address,
                'strategy_port': strategy_port,
                'symbol': symbol,
                'frequency': frequency
            }
        }

        response = {}

        # relay subscription request to the interface,
        # then relay the response back to the strategy
        message_to_address(interface_address,
                           interface_port,
                           query,
                           True,
                           lambda res: self.subscribe_callback(response, res))

        return response

    def unsubscribe_callback(self, response, res):
        response['status'] = res['status']
        if response['status'] == 'SUCCESS':
            self.logger.debug('Unsubscription made successfully!')
            response['data'] = res['data']
        elif response['status'] == 'FAIL':
            self.logger.error('Error during unsubscription: %s' % res['message'])
            response['message'] = res['message']
        else:
            self.logger.error('Invalid status in INTERFACE_UNSUBSCRIBE response: %s' % res['status'])

    def unsubscribe(self, request_data):
        """
        Unsubscribe from a specified subscription.
        Like the subscription handler, pretty much forwards the request to the appropriate
        interface.

        :param request_data: contains data specifying the subscription:
            sub_handle: unique handle of the subscription
        """
        sub_handle = request_data['sub_handle']
        market_interface_id = request_data['market_interface_id']

        # handle unknown market interface
        if market_interface_id not in self.MANAGER.market_interfaces:
            self.logger.error('Unknown market interface %s' % market_interface_id)
            return {
                'status': 'FAIL',
                'message': 'Unknown market interface %s' % market_interface_id
            }

        # get interface address and port
        interface_address = self.MANAGER.market_interfaces[market_interface_id]['address']
        interface_port = self.MANAGER.market_interfaces[market_interface_id]['port']

        # query to interface
        query = {
            'query': 'INTERFACE_UNSUBSCRIBE',
            'data': {
                'sub_handle': sub_handle
            }
        }

        response = {}

        # relay unsubscription request to the interface,
        # then relay the response back to the strategy
        message_to_address(interface_address,
                           interface_port,
                           query,
                           True,
                           lambda res: self.unsubscribe_callback(response, res))

        return response
