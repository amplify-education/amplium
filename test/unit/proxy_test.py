"""Unit testing for the proxy.py"""
import json
import unittest
import requests

from mock import patch, MagicMock

from amplium.api import proxy
from amplium.api.exceptions import NoAvailableGridsException, NoAvailableCapacityException
from amplium.app import app

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


GRID_NODE_INFO = {
    "inactivityTime": 258610,
    "internalKey": "86723674-e6c4-4c0b-84e1-9d9b59250134",
    "msg": "slot found !",
    "proxyId": "http://10.101.9.142:5555",
    "session": "6df13e64df39c3d21f65380a0af04213",
    "success": True
}


@patch('time.sleep', MagicMock())
class ProxyUnitTests(unittest.TestCase):
    """Unit testing for the proxy.py"""

    def setUp(self):
        self.app = app.app.test_client()
        self.app.testing = True

    @patch('amplium.api.proxy.GRID_HANDLER.get_base_url', MagicMock(return_value='http://test_host1:1234'))
    @patch('amplium.api.proxy.send_request')
    def test_create_session(self, mock_request):
        """Tests the create session on a successful create"""
        mock_request_data = {"made_up_stuff": "foo"}
        proxy.create_session(mock_request_data)
        mock_request.assert_called_once_with(
            'POST',
            data=mock_request_data,
            url='http://test_host1:1234/wd/hub/session'
        )

    @patch('amplium.api.proxy.GRID_HANDLER.unroll_session_id',
           MagicMock(return_value=("test_session_id", "http://test_node_1:1234")))
    @patch('amplium.api.proxy.send_request')
    def test_get_session_info(self, mock_request):
        """Test a correct request while getting Grid node info from session_id."""
        proxy.get_session_info(session_id="ea88098b344441de443-4d7f48c3f749a")
        mock_request.assert_called_once_with(
            'GET',
            "test_session_id",
            url='http://test_node_1:1234/grid/api/testsession?session=test_session_id'
        )

    @patch('amplium.api.proxy.GRID_HANDLER.get_base_url', MagicMock(return_value='http://test_host_1:1234'))
    @patch('amplium.api.proxy.SESSION')
    def test_create_session_send_request(self, mock_session):
        """Test the send request from create session"""
        test_data = {'desiredCapabilities': {'amplium:useSauceLabs': False}}
        test_url = 'http://test_host_1:1234/wd/hub/session'
        proxy.create_session(test_data)
        mock_session.request.assert_called_once_with(json=test_data, method='POST', url=test_url)

    @patch('amplium.api.proxy.GRID_HANDLER.get_base_url', MagicMock(side_effect=NoAvailableGridsException))
    @patch('amplium.api.proxy.send_request', MagicMock(return_value={}))
    def test_create_session_if_no_grids(self):
        """Tests if we create a session with no grids available"""
        test_data = {'desiredCapabilities': {'amplium:useSauceLabs': False}}
        response = self.app.post(
            "/proxy/session",
            data=json.dumps(test_data),
            content_type='application/json'
        )
        response_json = json.loads(response.data)

        self.assertIn("value", response_json.keys())
        self.assertEquals(response_json["status"], "ERROR")
        self.assertEquals(response.status_code, 429)

    @patch('amplium.api.proxy.GRID_HANDLER.get_base_url', MagicMock(side_effect=NoAvailableCapacityException))
    @patch('amplium.api.proxy.send_request', MagicMock(return_value={}))
    def test_create_session_if_no_capacity(self):
        """Tests if we create a session with no capacity available"""
        test_data = {'desiredCapabilities': {'amplium:useSauceLabs': False}}
        response = self.app.post(
            "/proxy/session",
            data=json.dumps(test_data),
            content_type='application/json'
        )
        response_json = json.loads(response.data)

        self.assertIn("value", response_json.keys())
        self.assertEquals(response_json["status"], "ERROR")
        self.assertEquals(response.status_code, 429)

    @patch('amplium.api.proxy.GRID_HANDLER.get_base_url', MagicMock(side_effect=KeyError))
    @patch('amplium.api.proxy.send_request', MagicMock(return_value={}))
    @patch('kazoo.client.KazooClient.start', MagicMock())
    def def_test_general_exception(self):
        """Test if we create a session and get a general error"""
        test_data = {'desiredCapabilities': {}}
        response = self.app.post(
            "/proxy/session",
            data=json.dumps(test_data),
            content_type='application/json'
        )
        response_json = json.loads(response.data)

        self.assertIn("value", response_json.keys())
        self.assertEquals(response_json["status"], "ERROR")
        self.assertEquals(response.status_code, 500)

    @patch(
        'amplium.api.proxy.GRID_HANDLER.unroll_session_id',
        MagicMock(return_value=("test_session_id", "http://test_host_1:1234"))
    )
    @patch('amplium.api.proxy.SESSION')
    def test_delete_session(self, mock_session):
        """Tests the delete session"""
        proxy.delete_session('test_session_id')
        test_url = 'http://test_host_1:1234/wd/hub/session/test_session_id'
        mock_session.request.assert_called_once_with(method='DELETE', url=test_url, json=None)

    @patch(
        'amplium.api.proxy.GRID_HANDLER.unroll_session_id',
        MagicMock(return_value=("test_session_id", "http://test_host_1:1234"))
    )
    @patch('amplium.api.proxy.SESSION')
    def test_get_command(self, mock_session):
        """Tests the get command"""
        proxy.get_command('test_session_id', 'test_command')
        test_url = 'http://test_host_1:1234/wd/hub/session/test_session_id/test_command'
        mock_session.request.assert_called_once_with(json=None, method='GET', url=test_url)

    @patch(
        'amplium.api.proxy.GRID_HANDLER.unroll_session_id',
        MagicMock(return_value=("test_session_id", "http://test_host_1:1234"))
    )
    @patch('amplium.api.proxy.SESSION')
    def test_post_command(self, mock_session):
        """Tests the post command"""
        proxy.post_command('test_session_id', 'test_command', 'test_params')
        test_url = 'http://test_host_1:1234/wd/hub/session/test_session_id/test_command'
        mock_session.request.assert_called_once_with(json='test_params', method='POST', url=test_url)

    @patch(
        'amplium.api.proxy.GRID_HANDLER.unroll_session_id',
        MagicMock(return_value=("test_session_id", "http://test_host_1:1234"))
    )
    @patch('amplium.api.proxy.SESSION')
    def test_delete_command(self, mock_session):
        """Tests the delete command"""
        proxy.delete_command('test_session_id', 'test_command')
        test_url = 'http://test_host_1:1234/wd/hub/session/test_session_id/test_command'
        mock_session.request.assert_called_once_with(json=None, url=test_url, method='DELETE')

    @patch(
        'amplium.api.proxy.GRID_HANDLER.unroll_session_id',
        MagicMock(return_value=("test_session_id", "http://test_host_1:1234"))
    )
    @patch('amplium.api.proxy.SESSION')
    def test_request_wrapper_timeout(self, mock_session):
        """Tests the request wrapper's timeout exceptions"""
        mock_session.request.side_effect = requests.exceptions.Timeout(response=MagicMock(status_code=408))
        response = proxy.send_request(method='POST', data={'data': 'test'})
        self.assertEqual(response[0]['status'], 408)
