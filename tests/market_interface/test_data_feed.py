import unittest
import mock

from market_interface.data_feed import push_feed, feed_callback


class TestDataFeed(unittest.TestCase):
    @mock.patch("logging.getLogger")
    def setUp(self, mock_get_logger):
        self.logger = mock.Mock()
        mock_get_logger.return_value = self.logger

    @mock.patch("market_interface.data_feed.MessageSender")
    @mock.patch("time.sleep")
    def test_push_feed(self, mock_sleep, mock_message_sender):
        def side_effect(*args, **kwargs):
            del interface.subscriptions["test_sub"]
        mock_send_message = mock_message_sender.return_value.send_message
        mock_send_message.side_effect = side_effect

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

        mock_send_message.assert_called_once()
        mock_message_sender.return_value.close.assert_called_once()
        self.assertTupleEqual(({'query': 'MARKET_DATA_FEED', 'data': "test_data"}, False), mock_send_message.call_args[0][:-1])

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
