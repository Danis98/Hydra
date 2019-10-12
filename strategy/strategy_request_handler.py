import logging

from common.request_handler import RequestHandler

PONG_RESPONSE = {
    'status': 'SUCCESS',
    'data': 'PONG'
}


class StrategyRequestHandler(RequestHandler):
    def __init__(self, client_socket, strategy):
        super().__init__(client_socket)
        self.logger = logging.getLogger('strategy_request_handler')

        self.STRATEGY = strategy

        self.query_handlers = {
            'INIT': self.STRATEGY.on_init,
            'START': self.STRATEGY.on_start,
            'STOP': self.STRATEGY.on_stop,
            'REALLOCATE': self.STRATEGY.on_funds_reallocation,
            'PING': lambda data: PONG_RESPONSE
        }
