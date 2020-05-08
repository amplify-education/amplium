"""Unit testing for the tracekey.py"""
import unittest

import flask
from mock import patch, MagicMock

from amplium.utils import tracekey

app = flask.Flask(__name__)


class TraceKeyUnitTests(unittest.TestCase):
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

    def test_tracekey(self):
        """Tests tracekey if flask.g.tracekey is set,
        should return flask.g.tracekey's tracekey"""
        with app.test_request_context():
            flask.g.tracekey = 'test_tracekey'
            response = tracekey.tracekey()
            self.assertEqual(response, 'test_tracekey')

    @patch('uuid.uuid1', MagicMock(return_value='test_uuid'))
    def test_tracekey_original(self):
        """Tests if a tracekey.g has not been set,
        Returns a new generated uuid"""
        with app.test_request_context():
            response = tracekey.tracekey()
            self.assertEqual(response, 'test_uuid')

    def test_filter(self):
        """Tests the TracekeyFilter filter method. Should return true."""
        tracekey_class = tracekey.TracekeyFilter()
        response = tracekey_class.filter(MagicMock(tracekey='test'))
        self.assertEqual(response, True)

    def test_filter_request(self):
        """Tests if the flask has request context(). Should return true"""

        with app.test_request_context():
            tracekey_class = tracekey.TracekeyFilter()
            response = tracekey_class.filter(MagicMock(tracekey='test'))
            self.assertEqual(response, True)
