import logging

from common.api_server import ApiServer
from portfolio_manager.portfolio_request_handler import PortfolioRequestHandler


# TODO: implement component identification and authentication mechanisms


class PortfolioApiServer (ApiServer):
    """
    Main server thread for the portfolio.
    Runs in parallel with the main portfolio manager thread and handles
    incoming requests.
    """
    def __init__(self, host, port, portfolio_manager):
        """
        Initializes the server thread with the parameters needed for operation.

        :param host: address of the server
        :param port: port of the server
        :param portfolio_manager: parent portfolio manager, containing the data concerning
                                strategies and interfaces
        """
        super().__init__(host, port)
        self.logger = logging.getLogger('portfolio_api_server')
        self.logger.info('Portfolio api server created!')

        self.MANAGER = portfolio_manager

        self.subscriptions = {}

    def get_handler(self, client_socket):
        return PortfolioRequestHandler(client_socket, self.MANAGER)
