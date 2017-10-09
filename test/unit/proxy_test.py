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


@patch('time.sleep', MagicMock())
class ProxyUnitTests(unittest.TestCase):
    """Unit testing for the proxy.py"""

    def setUp(self):
        self.app = app.app.test_client()
        self.app.testing = True

    @patch('amplium.utils.dynamodb_handler.DynamoDBHandler.add_entry', MagicMock(return_value=True))
    @patch('amplium.api.proxy._get_base_url', MagicMock(return_value='http:test_host1:1234'))
    @patch('amplium.api.proxy.send_request', MagicMock(return_value={'sessionId': 1234}))
    def test_create_session(self):
        """Tests the create session on a successful create"""
        response = proxy.create_session({})
        self.assertEqual(response, {'sessionId': 1234})

    @patch('amplium.api.proxy._get_base_url', MagicMock(return_value='http://test_host_1:1234'))
    @patch('amplium.utils.dynamodb_handler.DynamoDBHandler.add_entry', MagicMock(return_value=True))
    @patch('amplium.api.proxy.SESSION')
    def test_create_session_send_request(self, mock_session):
        """Test the send request from create session"""
        test_data = {'desiredCapabilities': {'amplium:useSauceLabs': False}}
        test_url = 'http://test_host_1:1234/wd/hub/session'
        proxy.create_session(test_data)
        mock_session.request.assert_called_once_with(json=test_data, method='POST', url=test_url)

    @patch('amplium.api.proxy._get_base_url', MagicMock(side_effect=NoAvailableGridsException))
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

    @patch('amplium.api.proxy._get_base_url', MagicMock(side_effect=NoAvailableCapacityException))
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

    @patch('amplium.api.proxy._get_base_url', MagicMock(side_effect=KeyError))
    @patch('amplium.api.proxy.send_request', MagicMock(return_value={}))
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

    @patch('amplium.utils.dynamodb_handler.DynamoDBHandler.delete_entry', MagicMock(return_value=True))
    @patch('amplium.utils.dynamodb_handler.DynamoDBHandler.get_entry',
           MagicMock(return_value={'BaseUrl': 'http://test_host_1:1234'}))
    @patch('amplium.api.proxy.SESSION')
    def test_delete_session(self, mock_session):
        """Tests the delete session"""
        proxy.delete_session('test_session_id')
        test_url = 'http://test_host_1:1234/wd/hub/session/test_session_id'
        mock_session.request.assert_called_once_with(method='DELETE', url=test_url, json=None)

    @patch('amplium.utils.dynamodb_handler.DynamoDBHandler.get_entry',
           MagicMock(return_value={'BaseUrl': 'http://test_host_1:1234'}))
    @patch('amplium.api.proxy.SESSION')
    def test_get_command(self, mock_session):
        """Tests the get command"""
        proxy.get_command('test_session_id', 'test_command')
        test_url = 'http://test_host_1:1234/wd/hub/session/test_session_id/test_command'
        mock_session.request.assert_called_once_with(json=None, method='GET', url=test_url)

    @patch('amplium.utils.dynamodb_handler.DynamoDBHandler.get_entry',
           MagicMock(return_value={'BaseUrl': 'http://test_host_1:1234'}))
    @patch('amplium.api.proxy.SESSION')
    def test_post_command(self, mock_session):
        """Tests the post command"""
        proxy.post_command('test_session_id', 'test_command', 'test_params')
        test_url = 'http://test_host_1:1234/wd/hub/session/test_session_id/test_command'
        mock_session.request.assert_called_once_with(json='test_params', method='POST', url=test_url)

    @patch('amplium.utils.dynamodb_handler.DynamoDBHandler.get_entry',
           MagicMock(return_value={'BaseUrl': 'http://test_host_1:1234'}))
    @patch('amplium.api.proxy.SESSION')
    def test_delete_command(self, mock_session):
        """Tests the delete command"""
        proxy.delete_command('test_session_id', 'test_command')
        test_url = 'http://test_host_1:1234/wd/hub/session/test_session_id/test_command'
        mock_session.request.assert_called_once_with(json=None, url=test_url, method='DELETE')

    @patch('amplium.utils.dynamodb_handler.DynamoDBHandler.get_entry',
           MagicMock(return_value={'BaseUrl': 'http://test_host_1:1234'}))
    @patch('amplium.api.proxy.SESSION')
    def test_request_wrapper_timeout(self, mock_session):
        """Tests the request wrapper's timeout exceptions"""
        mock_session.request.side_effect = requests.exceptions.Timeout(response=MagicMock(status_code=408))
        response = proxy.send_request(method='POST', data={'data': 'test'})
        self.assertEqual(response[0]['message'], 'Timeout occurred while proxying')

    @patch('amplium.utils.dynamodb_handler.DynamoDBHandler.get_entry',
           MagicMock(return_value={'BaseUrl': 'http://test_host_1:1234'}))
    @patch('amplium.api.proxy.SESSION')
    def test_request_wrapper_httperror(self, mock_session):
        """Tests the httperror exception"""
        mock_session.request.side_effect = requests.exceptions.HTTPError(response=MagicMock(status_code=404))
        response = proxy.send_request(method='POST', data={'data': 'test'})
        self.assertEqual(response[0]['message'], 'Http error occurred while proxying')

    @patch('amplium.utils.zookeeper.ZookeeperGridNodeStatus.get_nodes',
           MagicMock(side_effect=mock_zookeeper_get_nodes))
    def test_get_ip_address(self):
        """Tests the get ip address"""
        response = proxy._get_ip_address()
        self.assertEqual(response[0], "test_host_2")

    @patch('amplium.utils.zookeeper.ZookeeperGridNodeStatus.get_nodes')
    def test_get_ip_address_total_capacity(self, mock_get_nodes):
        """Tests the compare for matching available capacities, highest total capacity should be chosen"""
        data = [
            {"host": "test_host_1", "port": 1234, 'available_capacity': 1, 'total_capacity': 1, 'queue': 0},
            {"host": "test_host_2", "port": 1234, 'available_capacity': 1, 'total_capacity': 2, 'queue': 0},
        ]
        mock_get_nodes.return_value = data
        response = proxy._get_ip_address()
        self.assertEqual(response[0], "test_host_2")

    @patch('amplium.utils.zookeeper.ZookeeperGridNodeStatus.get_nodes')
    def test_get_ip_address_queue(self, mock_get_nodes):
        """Tests the compare for matching available and total capacities, lowest queue should be chosen"""
        data = [
            {"host": "test_host_1", "port": 1234, 'available_capacity': 1, 'total_capacity': 1, 'queue': 0},
            {"host": "test_host_2", "port": 1234, 'available_capacity': 1, 'total_capacity': 1, 'queue': 1},
        ]
        mock_get_nodes.return_value = data
        response = proxy._get_ip_address()
        self.assertEqual(response[0], "test_host_1")

    @patch('amplium.utils.saucelabs_handler.get_sauce_url', MagicMock(return_value=''))
    @patch('amplium.utils.zookeeper.ZookeeperGridNodeStatus.get_nodes',
           MagicMock(side_effect=mock_zookeeper_get_nodes))
    def test_create_get_base_url_zookeeper(self):
        """Tests the get base url to get the zookeeper url with empty queue"""
        test_data = {'desiredCapabilities': {'amplium:useSauceLabs': False}}
        test_url = 'http://test_host_2:1234'
        response = proxy._get_base_url(test_data)
        self.assertEqual(response, test_url)

    @patch('amplium.utils.saucelabs_handler.get_sauce_url', MagicMock(return_value=''))
    @patch('amplium.utils.zookeeper.ZookeeperGridNodeStatus.get_nodes',
           MagicMock(side_effect=mock_zookeeper_get_nodes_filled_queue))
    def test_get_base_url_zookeeper_filled_queue(self):
        """Tests the get base url to get the zookeeper url with a filled queue"""
        test_data = {'desiredCapabilities': {'amplium:useSauceLabs': False}}
        test_url = 'http://test_host_3:1234'
        response = proxy._get_base_url(test_data)
        self.assertEqual(response, test_url)

    @patch('amplium.utils.saucelabs_handler.get_sauce_url', MagicMock(return_value=test_sauce_url))
    def test_create_get_base_url(self):
        """Tests the get base url if it gets the url sauce"""
        test_data = {'desiredCapabilities': {'amplium:useSauceLabs': True}}
        test_url = 'https://username:accesskey@ondemand.saucelabs.com:443'
        response = proxy._get_base_url(test_data)
        self.assertEqual(response, test_url)

    @patch('amplium.utils.saucelabs_handler.get_sauce_url', MagicMock(return_value=test_sauce_url))
    def test_create_get_base_url_session_required(self):
        """Tests the get base url with requiredCapabilities"""
        test_data = {'requiredCapabilities': {'amplium:useSauceLabs': True}}
        test_url = 'https://username:accesskey@ondemand.saucelabs.com:443'
        response = proxy._get_base_url(test_data)
        self.assertEqual(response, test_url)

    @patch('amplium.utils.zookeeper.ZookeeperGridNodeStatus.get_nodes',
           MagicMock(return_value=[]))
    def test_get_base_url_none(self):
        """Tests if _get_base receives None from ip_address"""
        test_data = {'desiredCapabilities': {'amplium:useSauceLabs': False}}
        self.assertRaises(NoAvailableGridsException, proxy._get_base_url, test_data)
