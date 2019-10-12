import pytest
import json
import mock
import strategy.strategy_request_handler as strat_handler


@pytest.fixture
@mock.patch('socket.socket')
def src_sock(mock_sock):
    return mock_sock


@pytest.fixture
@mock.patch('strategy.strategy_template.Strategy')
@mock.patch('logging.Logger')
def req_handler(mock_strat, mock_logger, src_sock):
    mock_strat.on_init.return_value = "init called"
    mock_strat.on_start.return_value = "start called"
    mock_strat.on_resume.return_value = "resume called"
    mock_strat.on_stop.return_value = "stop called"
    mock_strat.logger = mock_logger
    req_handler = strat_handler.StrategyRequestHandler(src_sock, mock_strat)
    return req_handler


def test_handle_init(req_handler, src_sock):
    msg = {
        'query': 'INIT',
        'data': {
            'message': 'TEST_INIT'
        }
    }
    src_sock.recv.return_value.decode.return_value = json.dumps(msg)
    req_handler.start()
    req_handler.join()
    req_handler.STRATEGY.on_init.assert_called_with(msg['data'])


def test_handle_start(req_handler, src_sock):
    msg = {
        'query': 'START',
        'data': {
            'message': 'TEST_START'
        }
    }
    src_sock.recv.return_value.decode.return_value = json.dumps(msg)
    req_handler.start()
    req_handler.join()
    req_handler.STRATEGY.on_start.assert_called_with(msg['data'])


def test_handle_stop(req_handler, src_sock):
    msg = {
        'query': 'STOP',
        'data': {
            'message': 'TEST_STOP'
        }
    }
    src_sock.recv.return_value.decode.return_value = json.dumps(msg)
    req_handler.start()
    req_handler.join()
    req_handler.STRATEGY.on_stop.assert_called_with(msg['data'])


def test_handle_resume(req_handler, src_sock):
    msg = {
        'query': 'RESUME',
        'data': {
            'message': 'TEST_RESUME'
        }
    }
    src_sock.recv.return_value.decode.return_value = json.dumps(msg)
    req_handler.start()
    req_handler.join()
    req_handler.STRATEGY.on_resume.assert_called_with(msg['data'])


def test_handle_unknown(req_handler, src_sock):
    msg = {
        'query': 'UNKNOWN',
        'data': {
            'message': 'SOMETHING SOMETHING'
        }
    }
    src_sock.recv.return_value.decode.return_value = json.dumps(msg)
    req_handler.start()
    req_handler.join()
    req_handler.logger.error.assert_called_with('Unknown request: %s' % msg['query'])


def test_ping(req_handler, src_sock):
    msg = {
        'query': 'PING',
        'data': {}
    }
    src_sock.recv.return_value.decode.return_value = json.dumps(msg)
    req_handler.start()
    req_handler.join()
    src_sock.send.assert_called_with(json.dumps(strat_handler.PONG_RESPONSE).encode())
