"""Unit testing for Datadog integration"""
import unittest

from datadog.api.exceptions import ClientError, ApiNotInitialized
from mock import patch, ANY

from amplium.utils.datadog_handler import DatadogHandler


class SauceUnitTests(unittest.TestCase):
    """Unit tests for the DatadogHandler"""

    @patch('amplium.utils.datadog_handler.initialize')
    def test_no_config(self, mock_initialize):
        """Datadog is not initialized without config"""
        DatadogHandler(config=None)

        self.assertFalse(mock_initialize.called)

    @patch('amplium.utils.datadog_handler.initialize')
    def test_has_config(self, mock_initialize):
        """Datadog is initialized with config"""
        DatadogHandler(config={"foo": "bar"})

        self.assertTrue(mock_initialize.called)

    @patch('amplium.utils.datadog_handler.api.Metric.send')
    def test_send_metric_happy(self, mock_send):
        """Send metric sends a metric"""
        handler = DatadogHandler(config=None)

        handler.send("foo", 1, "gauge")

        mock_send.assert_called_once_with(metric="foo", points=(ANY, 1), host=ANY, type="gauge", tags=None)

    @patch('amplium.utils.datadog_handler.api.Metric.send')
    def test_send_metric_client_error(self, mock_send):
        """Send metric does not blow up if Datadog returns a client error"""
        mock_send.side_effect = ClientError("", "", "")
        handler = DatadogHandler(config=None)

        handler.send("foo", 1, "gauge")

    @patch('amplium.utils.datadog_handler.api.Metric.send')
    def test_send_metric_not_initialized(self, mock_send):
        """Send metric does not blow up if Datadog was not initialized"""
        mock_send.side_effect = ApiNotInitialized()
        handler = DatadogHandler(config=None)

        handler.send("foo", 1, "gauge")
