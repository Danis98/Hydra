import logging

from common.api_server import ApiServer
from strategy.strategy_request_handler import StrategyRequestHandler


PONG_RESPONSE = {
    'status': 'SUCCESS',
    'data': 'PONG'
}


class StrategyApiServer (ApiServer):
    def __init__(self, host, port, strategy):
        """
        Initializes server, then starts listening for incoming connections.

        :param host: address of the server
        :param port: port of the server
        :param strategy: reference to the parent strategy, used to access its data
        """
        super().__init__(host, port)

        self.logger = logging.getLogger('strategy_server')

        self.STRATEGY = strategy

        self.logger.info('Strategy server started successfully')

    def get_handler(self, client_socket):
        return StrategyRequestHandler(client_socket, self.STRATEGY)
