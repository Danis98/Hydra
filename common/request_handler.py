import json
import logging
import threading

from common.messaging import message_to_socket, log_result

BUFFER_SIZE = 1024


class RequestHandler (threading.Thread):
    """
    Handles the assigned incoming request, then exits.
    Runs in its own thread, to not block other stuff.

    Request is composed of:
        query: ID of the request (string)
        data: json object with request-specific data

    Response message status:
        SUCCESS : request executed successfully, has data field
        FAIL : request could not be executed for some reason, specified in message field
    """
    def __init__(self, client_socket):
        """
        Initialize handler.

        :param client_socket: socket used for communication with the requester (usually the manager)
        """
        threading.Thread.__init__(self)
        self.logger = logging.getLogger('request_handler')
        self.logger.info('Handling request!')

        self.socket = client_socket

        self.query_handlers = {}

    def run(self):
        """
        Read the request, decide which handler to use, and call it.
        If a query is not recognized, a FAIL is sent back.
        """
        self.logger.debug('Handling request')

        # read request
        request = json.loads(self.socket.recv(BUFFER_SIZE).decode())

        self.logger.debug('Received %r' % request)

        # decide which handler function to call
        query = request['query']
        if query not in self.query_handlers:
            self.logger.error('Unknown request: %s' % request['query'])
            resp = {
                'status': 'FAIL',
                'message': 'API query not defined'
            }
            message_to_socket(self.socket,
                              'query_origin',
                              resp,
                              False,
                              lambda r: log_result(r))
        else:
            self.logger.info('Handling %s' % query)
            response = self.query_handlers[query](request['data'])
            if response is not None:
                message_to_socket(self.socket,
                                  'query_origin',
                                  response,
                                  False,
                                  lambda r: log_result(r))
        self.socket.close()
