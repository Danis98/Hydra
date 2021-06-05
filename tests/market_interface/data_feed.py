import unittest
import mock

from market_interface.data_feed import push_feed, feed_callback


class MyTestCase(unittest.TestCase):
    @mock.patch("logging.getLogger")
    def setUp(self, mock_get_logger):
        self.logger = mock.Mock()
        mock_get_logger.return_value = self.logger

    @mock.patch("market_interface.data_feed.message_to_address")
    @mock.patch("time.sleep")
    def test_push_feed(self, mock_sleep, mock_message_to_address):
        def side_effect(*args, **kwargs):
            del interface.subscriptions["test_sub"]
        mock_message_to_address.side_effect = side_effect

        interface = mock.Mock()
        interface.subscriptions = {
            "test_sub": {
                "strategy_address": 0,
                "strategy_port": 0,
                "frequency": 0
            }
        }
        interface.get_data.return_value = "test_data"

        push_feed(interface, "test_sub")

        mock_message_to_address.assert_called_once()
        self.assertTupleEqual((0, 0, {'query': 'MARKET_DATA_FEED', 'data': "test_data"}, False), mock_message_to_address.call_args[0][:-1])

    def test_feed_callback_success(self):
        interface = mock.Mock()
        interface.subscriptions = {"test_sub": {}}
        resp = {"status": "SUCCESS", "message": "test"}
        feed_callback(interface, "test_sub", resp, self.logger)
        self.assertEqual(interface.subscriptions, {"test_sub": {}})

    def test_feed_callback_fail(self):
        interface = mock.Mock()
        interface.subscriptions = {"test_sub": {}}
        resp = {"status": "FAIL", "message": "test"}
        feed_callback(interface, "test_sub", resp, self.logger)
        self.assertEqual(interface.subscriptions, {})


if __name__ == '__main__':
    unittest.main()
