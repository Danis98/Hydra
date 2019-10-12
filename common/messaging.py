import json
import socket
import logging


logger = logging.getLogger('common_request')

BUFFER_SIZE = 1024


def log_result(r):
    if r['status'] == 'SUCCESS':
        return 'Message sent/Request completed successfully!'
    elif r['status'] == 'FAIL':
        return 'Failure: %s' % r['message']
    else:
        return 'Failure: invalid status %s' % r['status']


def message_to_socket(dest_sock, dest_name, query, expect_response, callback):
    """
    Send request to socket, and execute the callback with the response.
    Used when we already have the socket, esp. when we want to send a response

    :param dest_sock: socket connected to the dest
    :param dest_name: string descriptor of the destination, used for debugging and logging
    :param query: body of the request
    :param expect_response: True if a response is expected from dest
    :param callback:function to call after execution, necessary because we could be running
                    in a separate thread
    """
    try:
        dest_sock.send(json.dumps(query).encode())
    except socket.timeout:
        logger.error('Connection timed out with %s during request' % dest_name)
        resp = {
            'status': 'FAIL',
            'message': 'Connection timed out with %s during request' % dest_name
        }
        callback(resp)
        return
    if expect_response:
        try:
            resp = json.loads(dest_sock.recv(BUFFER_SIZE).decode())

            # call appropriate callback
            if resp['status'] == 'FAIL':
                callback(resp)
            elif resp['status'] == 'SUCCESS':
                callback(resp)
        except socket.error as e:
            logger.error('Could not get response from %s: %s' % (dest_name, e))
            resp = {
                'status': 'FAIL',
                'message': 'Could not get response from %s: %s' % (dest_name, e)
            }
            callback(resp)
            return
        except json.JSONDecodeError as e:
            logger.error('Could not decode response from %s: %s' % (dest_name, e))
            resp = {
                'status': 'FAIL',
                'message': 'Could not decode response from %s: %s' % (dest_name, e)
            }
            callback(resp)
            return

    else:
        resp = {
            'status': 'SUCCESS',
            'data': {}
        }
        callback(resp)


def message_to_address(dest_address, dest_port, query, expect_response, callback):
    """
    Send request to the specified dest address and port,
    and execute the callback with the response.
    Used for one-off requests.

    :param dest_address: address of the dest
    :param dest_port: port of the server
    :param query: body of the request
    :param expect_response: True if a response is expected from dest
    :param callback: function to call after execution, necessary because we could be running
                    in a separate thread
    """
    dest_name = '%r:%r' % (dest_address, dest_port)

    # connect to manager
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    try:
        s.connect((dest_address, dest_port))
    except ConnectionRefusedError:
        logger.error('Could not connect to %s' % dest_name)
        resp = {
            'status': 'FAIL',
            'message': 'Could not connect to %s' % dest_name
        }
        callback(resp)
        return

    # send request
    message_to_socket(s, dest_name, query, expect_response, callback)
