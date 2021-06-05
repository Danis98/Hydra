import json
import socket
import logging

BUFFER_SIZE = 1024


def log_result(r, logger):
    if 'status' not in r:
        logger.error('Failure: Response object is malformed: status missing')
    elif r['status'] == 'SUCCESS':
        logger.debug('Message sent/Request completed successfully!')
    elif r['status'] == 'FAIL':
        logger.error('Failure: %s' % (r['message'] if 'message' in r else '[NO ERROR MESSAGE]'))
    else:
        logger.error('Failure: invalid status %s' % r['status'])


class MessageSender:
    def __init__(self, address, port, sock=None):
        self.address, self.port = address, port
        self.descriptor = '%s:%d' % (address, port)
        self.connected = False
        self.logger = logging.getLogger('message_sender_%s' % self.descriptor)
        if sock is None:
            self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        else:
            self.socket = sock

    def _connect_socket(self):
        try:
            self.socket.connect((self.address, self.port))
            self.connected = True
            return {'status': 'SUCCESS'}
        except ConnectionRefusedError:
            self.logger.error('Could not connect to %s' % self.descriptor)
            return {
                'status': 'FAIL',
                'message': 'Could not connect to %s' % self.descriptor
            }

    def _send_payload(self, payload):
        try:
            self.socket.send(json.dumps(payload).encode())
            return {'status': 'SUCCESS'}
        except socket.timeout:
            self.logger.error('Connection timed out with %s during request' % self.descriptor)
            return {
                'status': 'FAIL',
                'message': 'Connection timed out with %s during request' % self.descriptor
            }
        except ConnectionResetError:
            self.logger.error('Connection reset by %s during request' % self.descriptor)
            return {
                'status': 'FAIL',
                'message': 'Connection reset by %s' % self.descriptor
            }
        except BrokenPipeError:
            self.logger.error('Connection failed with %s during request' % self.descriptor)
            return {
                'status': 'FAIL',
                'message': 'Connection failed with %s during communication' % self.descriptor
            }

    def _get_response(self):
        try:
            resp = json.loads(self.socket.recv(BUFFER_SIZE).decode())
            return {'status': 'SUCCESS',
                    'data': resp}
        except socket.error as e:
            self.logger.error('Could not get response from %s: %s' % (self.descriptor, e))
            return {
                'status': 'FAIL',
                'message': 'Could not get response from %s: %s' % (self.descriptor, e)
            }
        except json.JSONDecodeError as e:
            self.logger.error('Could not decode response from %s: %s' % (self.descriptor, e))
            return {
                'status': 'FAIL',
                'message': 'Could not decode response from %s: %s' % (self.descriptor, e)
            }

    def send_message(self, payload, expect_response, callback):
        """
        Send message, and execute the callback with the response.

        :param payload: body of the request
        :param expect_response: True if a response is expected from dest
        :param callback: callback, called with response dict,
                status can be FAIL (message contains error message) or SUCCESS (data contain requested data)
        """

        # connect to manager if not connected
        if not self.connected:
            conn_res = self._connect_socket()
            if conn_res['status'] == 'FAIL':
                callback(conn_res)
                return

        # send payload
        send_res = self._send_payload(payload)
        if send_res['status'] == 'FAIL':
            callback(send_res)
            return

        if expect_response:
            recv_resp = self._get_response()
            callback(recv_resp)
        else:
            callback({'status': 'SUCCESS'})

    def close(self):
        self.socket.close()
        self.connected = False
