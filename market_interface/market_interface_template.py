import logging
import threading

logger = logging.getLogger('market_interface')


class WebsocketHandler (threading.Thread):
    def __init__(self):
        threading.Thread.__init__(self)

    def run(self):
        pass


class MarketInterface:
    def __init__(self):
        pass

    def make_rest_request(self):
        pass

    def create_websocket_stream(self):
        pass

    def send_websocket_command(self, websocket, payload):
        pass

    def on_websocket_recv(self, msg):
        pass
