import logging

from common.api_server import ApiServer
from market_interface.market_interface_request_handler import MarketInterfaceRequestHandler


class MarketInterfaceApiServer (ApiServer):
    def __init__(self, host, port, interface):
        """
        Initialize the interface server.

        :param host: address of the server
        :param port: port of the server
        :param interface: reference to the parent interface, used to modify data in it
        """
        super().__init__(host, port)
        self.logger = logging.getLogger('interface_api')

        self.INTERFACE = interface

        self.logger.info('Interface server started successfully')

    def get_handler(self, client_socket):
        return MarketInterfaceRequestHandler(client_socket, self.INTERFACE)
