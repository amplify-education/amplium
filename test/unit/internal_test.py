"""Tests the interal.py"""
import unittest

from mock import patch, MagicMock

from amplium.api import internal


class InternalUnitTests(unittest.TestCase):
    """Tests the internal.py"""

    @patch('amplium.ZOOKEEPER.get_nodes', MagicMock(return_value={}))
    def test_get_status(self):
        """Tests the get status function"""
        result = internal.get_status()
        self.assertEqual(result['status'], 'OK')
