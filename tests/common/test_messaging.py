import mock
import json
import socket
import unittest
from common.messaging import log_result, MessageSender


class TestLogResult(unittest.TestCase):
    @mock.patch("logging.getLogger")
    def setUp(self, mock_get_logger):
        self.logger = mock.Mock()
        mock_get_logger.return_value = self.logger

    def test_log_result_malformed(self):
        res = {}
        log_result(res, self.logger)
        self.logger.error.assert_called_once_with('Failure: Response object is malformed: status missing')

    def test_log_result_invalid(self):
        res = {'status': 'INVALID_GIBBERISH'}
        log_result(res, self.logger)
        self.logger.error.assert_called_once_with('Failure: invalid status INVALID_GIBBERISH')

    def test_log_result_success(self):
        res = {'status': 'SUCCESS'}
        log_result(res, self.logger)
        self.logger.debug.assert_called_once_with('Message sent/Request completed successfully!')

    def test_log_result_fail_msg(self):
        res = {'status': 'FAIL', 'message': 'test error'}
        log_result(res, self.logger)
        self.logger.error.assert_called_once_with('Failure: test error')

    def test_log_result_fail_no_msg(self):
        res = {'status': 'FAIL'}
        log_result(res, self.logger)
        self.logger.error.assert_called_once_with('Failure: [NO ERROR MESSAGE]')


class TestMessageSender(unittest.TestCase):
    @mock.patch("logging.getLogger")
    def setUp(self, mock_get_logger):
        self.logger = mock.Mock()
        mock_get_logger.return_value = self.logger
        sock = mock.Mock()
        self.messageSender = MessageSender("address", 0, sock)

    def test__connect_socket_success(self):
        self.assertEqual(self.messageSender._connect_socket(), {'status': 'SUCCESS'})
        self.assertTrue(self.messageSender.connected)

    def test__connect_socket_fail(self):
        self.messageSender.socket.connect.side_effect = ConnectionRefusedError
        self.assertEqual(self.messageSender._connect_socket(),
                         {'status': 'FAIL',
                          'message': 'Could not connect to address:0'})
        self.assertFalse(self.messageSender.connected)

    @mock.patch("json.dumps")
    def test__send_payload(self, mock_dumps):
        self.assertEqual(self.messageSender._send_payload("test"), {'status': 'SUCCESS'})

    @mock.patch("json.dumps")
    def test__send_payload_timeout(self, mock_dumps):
        self.messageSender.socket.send.side_effect = socket.timeout
        self.assertEqual(self.messageSender._send_payload("test"),
                         {'status': 'FAIL',
                          'message': 'Connection timed out with address:0 during request'})

    @mock.patch("json.dumps")
    def test__send_payload_connection_reset(self, mock_dumps):
        self.messageSender.socket.send.side_effect = ConnectionResetError
        self.assertEqual(self.messageSender._send_payload("test"),
                         {'status': 'FAIL',
                          'message': 'Connection reset by address:0'})

    @mock.patch("json.dumps")
    def test__send_payload_broken_pipe(self, mock_dumps):
        self.messageSender.socket.send.side_effect = BrokenPipeError
        self.assertEqual(self.messageSender._send_payload("test"),
                         {'status': 'FAIL',
                          'message': 'Connection failed with address:0 during communication'})

    @mock.patch("json.loads")
    def test__get_response(self, mock_loads):
        mock_loads.return_value = "test_data"
        self.assertEqual(self.messageSender._get_response(), {'status': 'SUCCESS', "data": "test_data"})

    @mock.patch("json.loads")
    def test__get_response_socket_error(self, mock_loads):
        self.messageSender.socket.recv.side_effect = socket.error("test error")
        self.assertEqual(self.messageSender._get_response(),
                         {'status': 'FAIL',
                          'message': 'Could not get response from address:0: test error'})

    @mock.patch("json.loads")
    def test__get_response_decoder_error(self, mock_loads):
        m = mock.Mock()
        m.count.return_value = 0
        m.rfind.return_value = 0
        mock_loads.side_effect = json.JSONDecodeError("test error", m, 0)
        self.assertEqual(self.messageSender._get_response(),
                         {'status': 'FAIL',
                          'message': 'Could not decode response from address:0: test error: line 1 column 0 (char 0)'})

    @mock.patch("common.messaging.MessageSender._connect_socket")
    @mock.patch("common.messaging.MessageSender._send_payload")
    @mock.patch("common.messaging.MessageSender._get_response")
    def test_send_message_not_conn(self, mock_get_response, mock_send_payload, mock_connect_socket):
        res_succ = {'status': 'SUCCESS'}
        res_fail = {'status': 'FAIL', 'message': 'test error'}

        mock_connect_socket.return_value = res_succ
        mock_send_payload.return_value = res_succ
        mock_get_response.return_value = res_succ
        mock_callback = mock.Mock()

        self.messageSender.send_message("TEST", True, mock_callback)

        mock_connect_socket.assert_called_once()
        mock_send_payload.assert_called_once_with("TEST")
        mock_get_response.assert_called_once()
        mock_callback.assert_called_once_with(res_succ)

    @mock.patch("common.messaging.MessageSender._connect_socket")
    @mock.patch("common.messaging.MessageSender._send_payload")
    @mock.patch("common.messaging.MessageSender._get_response")
    def test_send_message_conn(self, mock_get_response, mock_send_payload, mock_connect_socket):
        res_succ = {'status': 'SUCCESS'}
        res_fail = {'status': 'FAIL', 'message': 'test error'}

        mock_connect_socket.return_value = res_succ
        mock_send_payload.return_value = res_succ
        mock_get_response.return_value = res_succ
        mock_callback = mock.Mock()

        self.messageSender.connected = True
        self.messageSender.send_message("TEST", True, mock_callback)

        mock_connect_socket.assert_not_called()
        mock_send_payload.assert_called_once_with("TEST")
        mock_get_response.assert_called_once()
        mock_callback.assert_called_once_with(res_succ)

    @mock.patch("common.messaging.MessageSender._connect_socket")
    @mock.patch("common.messaging.MessageSender._send_payload")
    @mock.patch("common.messaging.MessageSender._get_response")
    def test_send_message_conn_fail(self, mock_get_response, mock_send_payload, mock_connect_socket):
        res_succ = {'status': 'SUCCESS'}
        res_fail = {'status': 'FAIL', 'message': 'test error'}

        mock_connect_socket.return_value = res_fail
        mock_send_payload.return_value = res_succ
        mock_get_response.return_value = res_succ
        mock_callback = mock.Mock()

        self.messageSender.send_message("TEST", True, mock_callback)

        mock_connect_socket.assert_called_once()
        mock_send_payload.assert_not_called()
        mock_get_response.assert_not_called()
        mock_callback.assert_called_once_with(res_fail)

    @mock.patch("common.messaging.MessageSender._connect_socket")
    @mock.patch("common.messaging.MessageSender._send_payload")
    @mock.patch("common.messaging.MessageSender._get_response")
    def test_send_message_send_fail(self, mock_get_response, mock_send_payload, mock_connect_socket):
        res_succ = {'status': 'SUCCESS'}
        res_fail = {'status': 'FAIL', 'message': 'test error'}

        mock_connect_socket.return_value = res_succ
        mock_send_payload.return_value = res_fail
        mock_get_response.return_value = res_succ
        mock_callback = mock.Mock()

        self.messageSender.send_message("TEST", True, mock_callback)

        mock_connect_socket.assert_called_once()
        mock_send_payload.assert_called_once_with("TEST")
        mock_get_response.assert_not_called()
        mock_callback.assert_called_once_with(res_fail)

    @mock.patch("common.messaging.MessageSender._connect_socket")
    @mock.patch("common.messaging.MessageSender._send_payload")
    @mock.patch("common.messaging.MessageSender._get_response")
    def test_send_message_resp_fail(self, mock_get_response, mock_send_payload, mock_connect_socket):
        res_succ = {'status': 'SUCCESS'}
        res_fail = {'status': 'FAIL', 'message': 'test error'}

        mock_connect_socket.return_value = res_succ
        mock_send_payload.return_value = res_succ
        mock_get_response.return_value = res_fail
        mock_callback = mock.Mock()

        self.messageSender.send_message("TEST", True, mock_callback)

        mock_connect_socket.assert_called_once()
        mock_send_payload.assert_called_once_with("TEST")
        mock_get_response.assert_called_once()
        mock_callback.assert_called_once_with(res_fail)

    @mock.patch("common.messaging.MessageSender._connect_socket")
    @mock.patch("common.messaging.MessageSender._send_payload")
    @mock.patch("common.messaging.MessageSender._get_response")
    def test_send_message_resp_not_exp(self, mock_get_response, mock_send_payload, mock_connect_socket):
        res_succ = {'status': 'SUCCESS'}
        res_fail = {'status': 'FAIL', 'message': 'test error'}

        mock_connect_socket.return_value = res_succ
        mock_send_payload.return_value = res_succ
        mock_get_response.return_value = res_succ
        mock_callback = mock.Mock()

        self.messageSender.send_message("TEST", False, mock_callback)

        mock_connect_socket.assert_called_once()
        mock_send_payload.assert_called_once_with("TEST")
        mock_get_response.assert_not_called()
        mock_callback.assert_called_once_with(res_succ)

    def test_close(self):
        self.messageSender.connected = True
        self.messageSender.close()
        self.messageSender.socket.close.assert_called_once()
        self.assertFalse(self.messageSender.connected)

if __name__ == '__main__':
    unittest.main()
