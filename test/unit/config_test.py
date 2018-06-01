"""Tests the config.py"""
import unittest

from mock import patch, MagicMock

from amplium import config


class ConfigUnitTests(unittest.TestCase):
    """Tests the internal.py"""

    @patch('amplium.config.os.getenv', MagicMock(return_value=None))
    def test_config_fail(self):
        """Tests the config function for failure"""
        with self.assertRaises(Exception):
            config.Config()

    @patch('amplium.config.open', MagicMock(return_value=None))
    @patch('amplium.config.os.getenv', MagicMock(return_value='test_path'))
    @patch('amplium.config.os.path.isfile', MagicMock(return_value=True))
    @patch('amplium.config.yaml.safe_load')
    def test_config_pass(self, mock_yaml):
        """Tests the config function for pass"""
        mock_yaml.return_value = {
            'zookeeper':
                {'host': 'test_host',
                 'port': 1234,
                 'selenium_grid_zookeeper_path': 'test_path'},
            'logging': {},
            'dynamodb': {
                "table_name": 'test_name'},
            'integrations': {
                'saucelabs': {
                    "username": 'user_name',
                    "accesskey": 'access_key'}}
        }
        results = config.Config()._config['zookeeper']
        self.assertEqual(results['host'], 'test_host')
        self.assertEqual(results['port'], 1234)
        self.assertEqual(results['selenium_grid_zookeeper_path'], 'test_path')

    @patch('amplium.config.yaml.safe_load')
    def test_empty_integration(self, mock_yaml):
        """Tests the config file when an integration is empty, integrations should be {}"""
        mock_yaml.return_value = {
            'zookeeper':
                {'host': 'test_host',
                 'port': 1234,
                 'selenium_grid_zookeeper_path': 'test_path'},
            'logging': {},
            'dynamodb': {
                "table_name": 'test_name'},
            'integrations': None
        }

        results = config.Config()._config['integrations']
        self.assertEqual(results, {})

    @patch('amplium.config.yaml.safe_load')
    def test_no_integration(self, mock_yaml):
        """Tests the config file when no integration is given, integrations should be {}"""
        mock_yaml.return_value = {
            'zookeeper':
                {'host': 'test_host',
                 'port': 1234,
                 'selenium_grid_zookeeper_path': 'test_path'},
            'logging': {},
            'dynamodb': {
                "table_name": 'test_name'}
        }

        results = config.Config()._config['integrations']
        self.assertEqual(results, {})
