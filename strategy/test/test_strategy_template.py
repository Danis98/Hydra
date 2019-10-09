import pytest
import mock
import json

from strategy.strategy_template import Strategy


@pytest.fixture()
@mock.patch('logging.Logger')
def strat(mock_logger):
    config ={
        "host": "TEST_HOST",
        "port": 7357,
        "manager_address": "TEST_HOST",
        "manager_port": 7357
    }
    s = Strategy('TEST_STRAT', 'TEST_LIVE', config)
    s.logger = mock_logger
    return s


@mock.patch('strategy.strategy_template.send_manager_query')
def test_register(mock_send, strat):
    strat.register()
    mock_send.assert_called_with(
        strat.MANAGER_ADDRESS,
        strat.MANAGER_PORT,
        {
            'query': 'REGISTER_STRATEGY',
            'data': {
                'strategy_id': strat.STRATEGY_ID,
                'strategy_address': strat.HOST,
                'strategy_port': strat.PORT,
                'mode': strat.MODE,
            }
        },
        strat.register_callback
    )


@mock.patch('strategy.strategy_template.send_manager_query')
def test_subscribe_success(mock_send, strat):
    market_interface_id = 'TEST_INTERFACE'
    symbol = 'MONEY'
    frequency = 'always'
    sub_handle = 'TEST_SUB_HANDLE'
    resp = {
        'status': 'SUCCESS',
        'data': {
            'subscription_handle': sub_handle
        }
    }

    mock_send.side_effect = lambda *args: strat.subscribe_callback(resp, market_interface_id)

    strat.subscribe(market_interface_id, symbol, frequency)
    assert len(strat.subscriptions) == 1
    assert strat.subscriptions[sub_handle] == {'market_interface_id': market_interface_id}


@mock.patch('strategy.strategy_template.send_manager_query')
def test_subscribe_fail(mock_send, strat):
    market_interface_id = 'TEST_INTERFACE'
    symbol = 'MONEY'
    frequency = 'always'
    resp = {
        'status': 'FAIL',
        'message': 'U DUN GOOFED'
    }

    mock_send.side_effect = lambda *args: strat.subscribe_callback(resp, market_interface_id)

    strat.subscribe(market_interface_id, symbol, frequency)
    strat.logger.error.assert_called_with('Could not subscribe to data feed: %s' % resp['message'])
    assert len(strat.subscriptions) == 0


@mock.patch('strategy.strategy_template.send_manager_query')
def test_unsubscribe_success(mock_send, strat):
    sub_handle = 'TEST_SUB_HANDLE'
    market_interface_id = 'TEST_INTERFACE'
    resp = {
        'status': 'SUCCESS',
        'data': {}
    }

    mock_send.side_effect = lambda *args: strat.unsubscribe_callback(resp, sub_handle)
    strat.subscriptions[sub_handle] = {
        'market_interface_id': market_interface_id
    }
    strat.unsubscribe(sub_handle)

    assert len(strat.subscriptions) == 0


@mock.patch('strategy.strategy_template.send_manager_query')
def test_unsubscribe_fail(mock_send, strat):
    sub_handle = 'TEST_SUB_HANDLE'
    market_interface_id = 'TEST_INTERFACE'
    resp = {
        'status': 'FAIL',
        'message': 'U DUN GOOFED'
    }

    mock_send.side_effect = lambda *args: strat.unsubscribe_callback(resp, sub_handle)
    strat.subscriptions[sub_handle] = {
        'market_interface_id': market_interface_id
    }
    strat.unsubscribe(sub_handle)

    strat.logger.error.assert_called_with('Could not unsubscribe to data feed: %s' % resp['message'])
    assert len(strat.subscriptions) == 1


@mock.patch('strategy.strategy_template.send_manager_query')
def test_unsubscribe_all(mock_send, strat):
    sub_len = 10
    market_interface_id = 'TEST_INTERFACE'
    resp = {
        'status': 'SUCCESS',
        'data': {}
    }
    for i in range(sub_len):
        strat.subscriptions['TEST_SUB%d' % i] = {
            'market_interface_id': market_interface_id
        }

    mock_send.side_effect = lambda *args: strat.unsubscribe_callback(resp, 'TEST_SUB%d' % (mock_send.call_count-1))
    strat.unsubscribe_all()
    assert mock_send.call_count == sub_len


def test_get_bulk_data(strat):
    pass


def test_get_current_data(strat):
    pass
