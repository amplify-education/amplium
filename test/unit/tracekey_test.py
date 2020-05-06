"""Unit testing for the tracekey.py"""

import aiounittest
from aiounittest import futurized
from mock import patch, MagicMock

from amplium.utils import tracekey
from amplium.utils.tracekey import TRACE_KEY, trace_key_middleware


class TraceKeyUnitTests(aiounittest.AsyncTestCase):
    """Unit testing for the tracekey.py"""

    @patch('uuid.uuid1', MagicMock(return_value='test_uuid'))
    def test_generate_tracekey(self):
        """Tests the generate tracekey function for a test uuid"""
        response = tracekey.generate_tracekey()
        self.assertEqual(response, 'test_uuid')

    @patch('uuid.uuid1', MagicMock(return_value='test_uuid'))
    def test_generate_tracekey_original(self):
        """Tests if original tracekey is given,
         expects a combination of the original and new"""
        response = tracekey.generate_tracekey('test_original')
        self.assertEqual(response, 'test_original/test_uuid')

    async def test_tracekey(self):
        """Tests tracekey if tracekey is set. Should return context var's tracekey"""
        TRACE_KEY.set('test_tracekey')
        mock_request = MagicMock()
        mock_request.headers = {}
        await trace_key_middleware(mock_request, MagicMock(return_value=futurized(None)))
        self.assertEqual(TRACE_KEY.get(), 'test_tracekey')

    @patch('uuid.uuid1', MagicMock(return_value='test_uuid'))
    async def test_tracekey_original(self):
        """Tests if a tracekey has not been set. Should return a new generated uuid"""
        mock_request = MagicMock()
        mock_request.headers = {}
        await trace_key_middleware(mock_request, MagicMock(return_value=futurized(None)))
        self.assertEqual(TRACE_KEY.get(), 'test_uuid')

    def test_filter(self):
        """Tests the TracekeyFilter filter method. Should return true."""
        tracekey_class = tracekey.TracekeyFilter()
        response = tracekey_class.filter(MagicMock(tracekey='test'))
        self.assertEqual(response, True)

    def test_filter_request(self):
        """Tests if the flask has request context(). Should return true"""
        tracekey_class = tracekey.TracekeyFilter()
        response = tracekey_class.filter(MagicMock(tracekey='test'))
        self.assertEqual(response, True)
