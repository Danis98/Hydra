import socket
import logging
import json


def send_manager_query(manager_address, manager_port, query, callback):
    """
    Utility function used to perform several functions.
    Handles sending the request to the manager, then calls the appropriate callback.
    Usually used to send requests in a non-blocking way, by executing it in a separate thread.

    :param manager_address: address of the manager server
    :param manager_port: port of the server
    :param query: body of the request
    :param callback_success: function to call
    """
    logger = logging.getLogger('send_manager_query')

    # connect to manager
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    try:
        s.connect((manager_address, manager_port))
    except ConnectionRefusedError:
        logger.error('Could not connect to manager')
        resp = {
            'status': 'FAIL',
            'message': 'Could not connect to manager'
        }
        callback(resp)
        return

    # send request
    try:
        s.send(json.dumps(query).encode())
        resp = json.loads(s.recv(1024).decode())

        # call appropriate callback
        if resp['status'] == 'FAIL':
            callback(resp)
        elif resp['status'] == 'SUCCESS':
            callback(resp)

    except socket.timeout:
        logger.error('Connection timed out with manager during request')
        resp = {
            'status': 'FAIL',
            'message': 'Connection timed out with manager during request'
        }
        callback(resp)
        return
