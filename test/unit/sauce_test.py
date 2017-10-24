"""Unit testing for util/saucelabs_handler.py"""

import unittest

import requests_mock

from mock import patch, MagicMock

from amplium.api.exceptions import IntegrationNotConfigured, AmpliumException, NoAvailableCapacityException
from amplium.utils import saucelabs_handler


class SauceUnitTests(unittest.TestCase):
    """Unit tests for the sauce handler"""

    @patch('amplium.utils.saucelabs_handler.is_saucelabs_available', MagicMock(return_value=True))
    def test_success_get_sauce(self):
        """Tests if get sauce url returns a url"""
        response = saucelabs_handler.get_sauce_url()
        self.assertEqual(response, 'https://username:accesskey@ondemand.saucelabs.com:443')

    @patch('amplium.utils.saucelabs_handler.is_saucelabs_available', MagicMock(return_value=False))
    def test_fail_get_sauce(self):
        """Tests if SauceLabs is not available get exception"""
        self.assertRaises(NoAvailableCapacityException, saucelabs_handler.get_sauce_url)

    @patch('amplium.utils.saucelabs_handler.CONFIG')
    def test_none_get_sauce(self, mock_config):
        """Tests if the integrations was not setup correctly"""
        mock_config.integrations = {}
        self.assertRaises(IntegrationNotConfigured, saucelabs_handler.get_sauce_url)

    def test_is_saucelabs_requested(self):
        """Tests if the is SauceLabs requested is true"""
        test_session_data = {'Capabilities': {
            'amplium:useSauceLabs': True
        }}
        response = saucelabs_handler.is_saucelabs_requested(test_session_data, 'Capabilities')
        self.assertEqual(response, True)

    def test_is_not_saucelabs_requested(self):
        """Tests if the is SauceLabs requested is true"""
        test_session_data = {'Capabilities': {}}
        response = saucelabs_handler.is_saucelabs_requested(test_session_data, 'Capabilities')
        self.assertEqual(response, False)

    @requests_mock.Mocker()
    def test_saucelabs_available_happy(self, mock_requests):
        """Tests if SauceLabs is available with happy response"""
        mock_response = {
            "concurrency": {
                "ancestor": {
                    "allowed": {
                        "mac": 100,
                        "real_device": 30,
                        "manual": 100,
                        "overall": 100
                    },
                    "username": "FAKE_NAME",
                    "current": {
                        "overall": 0,
                        "mac": 0,
                        "manual": 0
                    }
                }
            }
        }

        mock_requests.get(requests_mock.ANY, json=mock_response)

        response = saucelabs_handler.is_saucelabs_available()

        self.assertTrue(response)

    @requests_mock.Mocker()
    def test_saucelabs_available_busy(self, mock_requests):
        """Tests if SauceLabs is available with busy response"""
        mock_response = {
            "concurrency": {
                "ancestor": {
                    "allowed": {
                        "mac": 100,
                        "real_device": 30,
                        "manual": 100,
                        "overall": 100
                    },
                    "username": "FAKE_NAME",
                    "current": {
                        "overall": 100,
                        "mac": 100,
                        "manual": 100
                    }
                }
            }
        }
        mock_requests.get(requests_mock.ANY, json=mock_response)

        response = saucelabs_handler.is_saucelabs_available()

        self.assertFalse(response)

    @requests_mock.Mocker()
    def test_saucelabs_available_unauthorized(self, mock_requests):
        """Tests if SauceLabs is available with unauthorized response"""
        mock_requests.get(requests_mock.ANY, status_code=401, json={})

        self.assertRaises(AmpliumException, saucelabs_handler.is_saucelabs_available)

    @requests_mock.Mocker()
    def test_saucelabs_available_error(self, mock_requests):
        """Tests if SauceLabs is available with error response"""
        mock_requests.get(requests_mock.ANY, status_code=500, json={})

        self.assertRaises(AmpliumException, saucelabs_handler.is_saucelabs_available)
