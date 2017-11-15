"""Unit testing for util/saucelabs_handler.py"""

import unittest

import requests
import requests_mock

from mock import MagicMock

from amplium import CONFIG
from amplium.api.exceptions import IntegrationNotConfigured, AmpliumException, NoAvailableCapacityException
from amplium.utils import saucelabs_handler


class SauceUnitTests(unittest.TestCase):
    """Unit tests for the sauce handler"""

    def setUp(self):
        self.session = requests.Session()
        self.saucelabs = saucelabs_handler.SauceLabsHandler(config=CONFIG, session=self.session)

    def test_success_get_sauce(self):
        """Tests if get sauce url returns a url"""
        self.saucelabs.is_saucelabs_available = MagicMock(return_value=True)
        response = self.saucelabs.get_sauce_url()
        self.assertEqual(response, 'https://username:accesskey@ondemand.saucelabs.com:443')

    def test_fail_get_sauce(self):
        """Tests if SauceLabs is not available get exception"""
        self.saucelabs.is_saucelabs_available = MagicMock(return_value=False)
        self.assertRaises(NoAvailableCapacityException, self.saucelabs.get_sauce_url)

    def test_none_get_sauce(self):
        """Tests if the integrations was not setup correctly"""
        self.saucelabs.config = MagicMock(integrations={})
        self.assertRaises(IntegrationNotConfigured, self.saucelabs.get_sauce_url)

    def test_is_saucelabs_requested(self):
        """Tests if the is SauceLabs requested is true"""
        response = self.saucelabs.is_saucelabs_requested({'amplium:useSauceLabs': True})
        self.assertEqual(response, True)

    def test_is_not_saucelabs_requested(self):
        """Tests if the is SauceLabs requested is true"""
        response = self.saucelabs.is_saucelabs_requested({})
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

        response = self.saucelabs.is_saucelabs_available()

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

        response = self.saucelabs.is_saucelabs_available()

        self.assertFalse(response)

    @requests_mock.Mocker()
    def test_saucelabs_available_unauthorized(self, mock_requests):
        """Tests if SauceLabs is available with unauthorized response"""
        mock_requests.get(requests_mock.ANY, status_code=401, json={})

        self.assertRaises(AmpliumException, self.saucelabs.is_saucelabs_available)

    @requests_mock.Mocker()
    def test_saucelabs_available_error(self, mock_requests):
        """Tests if SauceLabs is available with error response"""
        mock_requests.get(requests_mock.ANY, status_code=500, json={})

        self.assertRaises(AmpliumException, self.saucelabs.is_saucelabs_available)
