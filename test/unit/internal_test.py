"""Tests the interal.py"""
import unittest

from mock import patch, MagicMock

from amplium.api import internal


class InternalUnitTests(unittest.TestCase):
    """Tests the internal.py"""

    @patch('amplium.GRID_HANDLER.get_grid_info', MagicMock(return_value={"some": "data"}))
    def test_get_status(self):
        """Tests the get status function"""
        result, code = internal.get_status()
        self.assertEqual(result['status'], 'OK')
        self.assertEqual(code, 200)

    @patch('amplium.GRID_HANDLER.get_grid_info', MagicMock(return_value={}))
    def test_get_status_without_data(self):
        """Tests the get status function"""
        result, code = internal.get_status()
        self.assertEqual(result['status'], 'OK')
        self.assertEqual(code, 503)
