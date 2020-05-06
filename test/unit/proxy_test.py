"""Unit testing for the proxy.py"""
import unittest

import requests
import requests_mock
from mock import patch, MagicMock

from amplium.api import proxy

test_sauce_url = 'https://username:accesskey@ondemand.saucelabs.com:443'


def mock_zookeeper_get_nodes():
    """Mocks zookeeper.getNodes"""
    return [
        {"host": "test_host_1", "port": 1234, 'available_capacity': 1, 'total_capacity': 1, 'queue': 0},
        {"host": "test_host_2", "port": 1234, 'available_capacity': 2, 'total_capacity': 2, 'queue': 0},
    ]


def mock_zookeeper_get_nodes_filled_queue():
    """Mocks zookeeper.getNodes with different order"""
    return [
        {"host": "test_host_1", "port": 1234, 'available_capacity': 0, 'total_capacity': 3, 'queue': 1},
        {"host": "test_host_2", "port": 1234, 'available_capacity': 3, 'total_capacity': 3, 'queue': 0},
        {"host": "test_host_3", "port": 1234, 'available_capacity': 2, 'total_capacity': 3, 'queue': 0},
        {"host": "test_host_4", "port": 1234, 'available_capacity': 3, 'total_capacity': 3, 'queue': 0},
    ]


def get_request_data_matcher(data=None, text=None):
    """Create a matcher for use by requests mock to match request data"""
    def match_request_data(request):
        if data:
            return request.json() == data
        return request.text == ('"%s"' % text)
    return match_request_data


@patch('time.sleep', MagicMock())
class ProxyUnitTests(unittest.TestCase):
    """Unit testing for the proxy.py"""

    @patch('amplium.api.proxy.GRID_HANDLER.get_base_url', MagicMock(return_value='http://test_host1:1234'))
    @requests_mock.Mocker()
    def test_create_session(self, mock_requests):
        """Tests the create session on a successful create"""
        mock_request_data = {"made_up_stuff": "foo"}

        mock_requests.post(
            'http://test_host1:1234/wd/hub/session',
            json={},
            additional_matcher=get_request_data_matcher(mock_request_data)
        )

        proxy.create_session(mock_request_data)

    @patch('amplium.api.proxy.GRID_HANDLER.unroll_session_id',
           MagicMock(return_value=("test_session_id", "http://test_node_1:1234")))
    @requests_mock.Mocker()
    def test_get_session_info(self, mock_requests):
        """Test a correct request while getting Grid node info from session_id."""
        mock_requests.get(
            'http://test_node_1:1234/grid/api/testsession?session=test_session_id',
            json={}
        )

        proxy.get_session_info(session_id="ea88098b344441de443-4d7f48c3f749a")

    @patch('amplium.api.proxy.GRID_HANDLER.get_base_url', MagicMock(return_value='http://test_host_1:1234'))
    @requests_mock.Mocker()
    def test_create_session_send_request(self, mock_requests):
        """Test the send request from create session"""
        test_data = {'desiredCapabilities': {'amplium:useSauceLabs': False}}
        test_url = 'http://test_host_1:1234/wd/hub/session'

        mock_requests.post(
            test_url,
            json={},
            additional_matcher=get_request_data_matcher(test_data)
        )

        proxy.create_session(test_data)

    @patch(
        'amplium.api.proxy.GRID_HANDLER.unroll_session_id',
        MagicMock(return_value=("test_session_id", "http://test_host_1:1234"))
    )
    @requests_mock.Mocker()
    def test_delete_session(self, mock_requests):
        """Tests the delete session"""
        test_url = 'http://test_host_1:1234/wd/hub/session/test_session_id'

        mock_requests.delete(
            test_url,
            json={}
        )
        proxy.delete_session('test_session_id')

    @patch(
        'amplium.api.proxy.GRID_HANDLER.unroll_session_id',
        MagicMock(return_value=("test_session_id", "http://test_host_1:1234"))
    )
    @requests_mock.Mocker()
    def test_get_command(self, mock_requests):
        """Tests the get command"""
        test_url = 'http://test_host_1:1234/wd/hub/session/test_session_id/test_command'
        mock_requests.get(
            test_url,
            json={}
        )
        proxy.get_command('test_session_id', 'test_command')

    @patch(
        'amplium.api.proxy.GRID_HANDLER.unroll_session_id',
        MagicMock(return_value=("test_session_id", "http://test_host_1:1234"))
    )
    @requests_mock.Mocker()
    def test_post_command(self, mock_requests):
        """Tests the post command"""
        test_url = 'http://test_host_1:1234/wd/hub/session/test_session_id/test_command'
        mock_requests.post(
            test_url,
            json={},
            additional_matcher=get_request_data_matcher(text='test_params')
        )
        proxy.post_command('test_session_id', 'test_command', 'test_params')

    @patch(
        'amplium.api.proxy.GRID_HANDLER.unroll_session_id',
        MagicMock(return_value=("test_session_id", "http://test_host_1:1234"))
    )
    @requests_mock.Mocker()
    def test_delete_command(self, mock_requests):
        """Tests the delete command"""
        test_url = 'http://test_host_1:1234/wd/hub/session/test_session_id/test_command'

        mock_requests.delete(test_url, json={})

        proxy.delete_command('test_session_id', 'test_command')

    @patch(
        'amplium.api.proxy.GRID_HANDLER.unroll_session_id',
        MagicMock(return_value=("test_session_id", "http://test_host_1:1234"))
    )
    @requests_mock.Mocker()
    def test_request_wrapper_timeout(self, mock_requests):
        """Tests the request wrapper's timeout exceptions"""
        mock_requests.post(
            'http://test_host_1:1234/wd/hub/session/test_session_id',
            exc=requests.exceptions.Timeout(response=MagicMock(status_code=408)),
            additional_matcher=get_request_data_matcher(data={'data': 'test'})
        )

        response = proxy.send_request(method='POST', data={'data': 'test'})
        self.assertEqual(response[0]['status'], 408)
