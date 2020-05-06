"""Tests the interal.py"""
import json
import unittest

from mock import patch, MagicMock

from amplium.api import internal


class InternalUnitTests(unittest.TestCase):
    """Tests the internal.py"""

    @patch('amplium.GRID_HANDLER.get_grid_info', MagicMock(return_value={"some": "data"}))
    def test_get_status(self):
        """Tests the get status function"""
        response = internal.get_status()
        self.assertEqual(json.loads(response.text)['status'], 'OK')
        self.assertEqual(response.status, 200)

    @patch('amplium.GRID_HANDLER.get_grid_info', MagicMock(return_value={}))
    def test_get_status_without_data(self):
        """Tests the get status function"""
        response = internal.get_status()
        self.assertEqual(json.loads(response.text)['status'], 'OK')
        self.assertEqual(response.status, 503)
