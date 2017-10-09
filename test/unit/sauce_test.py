"""Unit testing for util/saucelabs_handler.py"""

import unittest

from amplium.api.exceptions import IntegrationNotConfigured
from amplium.utils import saucelabs_handler
from mock import patch


class SauceUnitTests(unittest.TestCase):
    """Unit tests for the sauce handler"""

    def test_success_get_sauce(self):
        """Tests if get sauce url returns a url"""
        response = saucelabs_handler.get_sauce_url()
        self.assertEqual(response, 'https://username:accesskey@ondemand.saucelabs.com:443')

    @patch('amplium.utils.saucelabs_handler.CONFIG')
    def test_none_get_sauce(self, mock_config):
        """Tests if the integrations was not setup correctly"""
        mock_config.integrations = {}
        self.assertRaises(IntegrationNotConfigured, saucelabs_handler.get_sauce_url)

    def test_is_saucelabs_requested(self):
        """Tests if the is saucelabs requested is true"""
        test_session_data = {'Capabilities': {
            'amplium:useSauceLabs': True
        }}
        response = saucelabs_handler.is_saucelabs_requested(test_session_data, 'Capabilities')
        self.assertEqual(response, True)

    def test_is_not_saucelabs_requested(self):
        """Tests if the is saucelabs requested is true"""
        test_session_data = {'Capabilities': {}}
        response = saucelabs_handler.is_saucelabs_requested(test_session_data, 'Capabilities')
        self.assertEqual(response, False)
