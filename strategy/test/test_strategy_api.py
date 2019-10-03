import pytest
import json
import mock
from strategy.strategy_api import StrategyApiServer


@pytest.fixture
@mock.patch('strategy.strategy_template.Strategy')
@mock.patch('socket.socket')
@mock.patch('logging.Logger')
def api_serv(mock_strat, mock_sock, mock_logger):
    mock_strat.on_init.return_value = "init called"
    mock_strat.on_start.return_value = "start called"
    mock_strat.on_resume.return_value = "resume called"
    mock_strat.on_stop.return_value = "stop called"
    mock_strat.socket = mock_sock
    mock_strat.logger = mock_logger
    mock_serv = StrategyApiServer('localhost', 7257, mock_strat)
    return mock_serv


@pytest.fixture
@mock.patch('socket.socket')
def src_sock(mock_sock):
    return mock_sock


def test_handle_init(api_serv, src_sock):
    msg = {
        'query': 'INIT',
        'data': {
            'message': 'TEST_INIT'
        }
    }
    src_sock.recv.return_value.decode.return_value = json.dumps(msg)
    api_serv.handle_request(src_sock)
    api_serv.STRATEGY.on_init.assert_called_with(msg['data'])


def test_handle_start(api_serv, src_sock):
    msg = {
        'query': 'START',
        'data': {
            'message': 'TEST_START'
        }
    }
    src_sock.recv.return_value.decode.return_value = json.dumps(msg)
    api_serv.handle_request(src_sock)
    api_serv.STRATEGY.on_start.assert_called_with(msg['data'])


def test_handle_stop(api_serv, src_sock):
    msg = {
        'query': 'STOP',
        'data': {
            'message': 'TEST_STOP'
        }
    }
    src_sock.recv.return_value.decode.return_value = json.dumps(msg)
    api_serv.handle_request(src_sock)
    api_serv.STRATEGY.on_stop.assert_called_with(msg['data'])


def test_handle_resume(api_serv, src_sock):
    msg = {
        'query': 'RESUME',
        'data': {
            'message': 'TEST_RESUME'
        }
    }
    src_sock.recv.return_value.decode.return_value = json.dumps(msg)
    api_serv.handle_request(src_sock)
    api_serv.STRATEGY.on_resume.assert_called_with(msg['data'])


def test_handle_unknown(api_serv, src_sock):
    msg = {
        'query': 'UNKNOWN',
        'data': {
            'message': 'SOMETHING SOMETHING'
        }
    }
    src_sock.recv.return_value.decode.return_value = json.dumps(msg)
    api_serv.handle_request(src_sock)
    api_serv.logger.error.assert_called_with('Unknown request: %s' % msg['query'])
