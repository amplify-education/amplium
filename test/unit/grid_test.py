"""Unit testing for the grid handler"""
import unittest

import requests
import requests_mock
from mock import patch, MagicMock

from amplium import CONFIG
from amplium.api.exceptions import NoAvailableGridsException, NoAvailableCapacityException
from amplium.models.grid_node_data import GridNodeData
from amplium.utils.grid_handler import GridHandler

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
        # self.app = app.app.test_client()
        # self.app.testing = True

        self.saucelabs = MagicMock()
        self.zookeeper = MagicMock()
        self.datadog = MagicMock()
        self.session = requests.Session()

        self.grid = GridHandler(
            config=CONFIG,
            discovery=self.zookeeper,
            datadog=self.datadog,
            saucelabs=self.saucelabs,
            session=self.session
        )

    def test_get_ip_address(self):
        """Tests the get ip address"""
        self.grid.get_grid_info = MagicMock(side_effect=mock_zookeeper_get_nodes)

        response = self.grid._get_selenium_grid()
        self.assertEqual(response[0], "test_host_2")

    def test_get_ip_address_total_capacity(self):
        """Tests the compare for matching available capacities, highest total capacity should be chosen"""
        data = [
            {"host": "test_host_1", "port": 1234, 'available_capacity': 1, 'total_capacity': 1, 'queue': 0},
            {"host": "test_host_2", "port": 1234, 'available_capacity': 1, 'total_capacity': 2, 'queue': 0},
        ]
        self.grid.get_grid_info = MagicMock(return_value=data)

        response = self.grid._get_selenium_grid()
        self.assertEqual(response[0], "test_host_2")

    def test_get_ip_address_queue(self):
        """Tests the compare for matching available and total capacities, lowest queue should be chosen"""
        data = [
            {"host": "test_host_1", "port": 1234, 'available_capacity': 1, 'total_capacity': 1, 'queue': 0},
            {"host": "test_host_2", "port": 1234, 'available_capacity': 1, 'total_capacity': 1, 'queue': 1},
        ]
        self.grid.get_grid_info = MagicMock(return_value=data)

        response = self.grid._get_selenium_grid()
        self.assertEqual(response[0], "test_host_1")

    def test_create_get_base_url_zookeeper(self):
        """Tests get base url for Zookeeper when the queue is empty"""
        self.saucelabs.is_saucelabs_requested.return_value = False
        self.grid.get_grid_info = MagicMock(side_effect=mock_zookeeper_get_nodes)

        test_data = {'desiredCapabilities': {'amplium:useSauceLabs': False}}
        test_url = 'http://test_host_2:1234'
        response = self.grid.get_base_url(test_data)
        self.assertEqual(response, test_url)

    def test_get_base_url_zookeeper_filled_queue(self):
        """Tests the get base url to get the zookeeper url with a filled queue"""
        self.saucelabs.is_saucelabs_requested.return_value = False
        self.grid.get_grid_info = MagicMock(side_effect=mock_zookeeper_get_nodes_filled_queue)

        test_data = {'desiredCapabilities': {'amplium:useSauceLabs': False}}
        test_url = 'http://test_host_3:1234'
        response = self.grid.get_base_url(test_data)
        self.assertEqual(response, test_url)

    def test_create_get_base_url(self):
        """Tests get base url for SauceLabs with desiredCapabilities"""
        self.saucelabs.get_sauce_url.return_value = ('username:accesskey@ondemand.saucelabs.com', '443')

        test_data = {'desiredCapabilities': {'amplium:useSauceLabs': True}}
        test_url = 'https://username:accesskey@ondemand.saucelabs.com:443'
        response = self.grid.get_base_url(test_data)
        self.assertEqual(response, test_url)

    def test_create_get_base_url_session_required(self):
        """Tests get base url for SauceLabs with requiredCapabilities"""
        self.saucelabs.get_sauce_url.return_value = ('username:accesskey@ondemand.saucelabs.com', '443')

        test_data = {'requiredCapabilities': {'amplium:useSauceLabs': True}}
        test_url = 'https://username:accesskey@ondemand.saucelabs.com:443'
        response = self.grid.get_base_url(test_data)
        self.assertEqual(response, test_url)

    def test_get_base_url_none(self):
        """Tests if _get_base receives None from ip_address"""
        self.zookeeper.get_nodes.return_value = []
        self.saucelabs.is_saucelabs_requested.return_value = False

        test_data = {'desiredCapabilities': {'amplium:useSauceLabs': False}}
        self.assertRaises(NoAvailableGridsException, self.grid.get_base_url, test_data)

    def test_retrieve_hash_before_inserted(self):
        """Tests that we can retrieve a hash for a grid before its inserted"""
        self.zookeeper.nodes = [GridNodeData(name=None, host="test_host_1", port=1234)]
        self.grid.retrieve_grid_url("518153ffa792841450eb8ba0b0a32d8fb5a1d216a8df1443152857fa0949e262")

    def test_unroll_session_id(self):
        """Tests that we can unroll our own session id into the original url and session id"""
        original_session_id = "terrible-fake_session-id"
        grid_url = "some text"

        our_session_id = self.grid.generate_session_id(session_id=original_session_id, grid_url=grid_url)

        self.assertEqual((original_session_id, grid_url), self.grid.unroll_session_id(our_session_id))

    def test_no_available_capacity_error(self):
        """Tests that we raise an exception if there is no available capacity"""
        data = [
            {"host": "test_host_1", "port": 1234, 'available_capacity': 0, 'total_capacity': 1, 'queue': 0},
        ]
        self.grid.get_grid_info = MagicMock(return_value=data)

        self.assertRaises(NoAvailableCapacityException, self.grid._get_selenium_grid)
        self.datadog.send.assert_called_once_with(
            metric='amplium.queue_length',
            metric_type='counter',
            value=1
        )

    @requests_mock.Mocker()
    def test_get_grid_info_happy_path(self, mock_requests):
        """Tests that get grid info works on the happy path"""
        self.zookeeper.nodes = [GridNodeData(name=None, host="test_host_1", port=1234)]
        self.grid.get_usage_per_browser_type = MagicMock(return_value={"total": 0, "breakdown": {}})
        self.grid.get_grid_hub_sessions_capacity = MagicMock(return_value=0)
        mock_response = {
            "newSessionRequestCount": 0
        }

        mock_requests.get(requests_mock.ANY, json=mock_response)

        response = self.grid.get_grid_info()
        self.assertEqual(
            response,
            [
                {
                    'total_capacity': 0,
                    'available_capacity': 0,
                    'queue': 0, 'host':
                    'test_host_1',
                    'browsers': {},
                    'port': 1234
                }
            ]
        )

    @requests_mock.Mocker()
    def test_find_ips_in_grid_console(self, mock_requests):
        """Tests that we can find all of the IPs inside of a grid console"""
        url = "https://test_url:443"
        mock_response = "asdasfasdasfasdasfasdasdasdasd id : %s dsadasdasdasdasd" % url

        mock_requests.get(requests_mock.ANY, text=mock_response)

        actual_urls = self.grid.get_all_registered_nodes_ip("http://this doesnt matter")

        self.assertEqual(actual_urls, [url])

    @requests_mock.Mocker()
    def test_calc_capacity_works(self, mock_requests):
        """Tests that we can calculate the capacity of a grid"""
        mock_response = {
            "request": {
                "configuration": {
                    "maxSession": 100
                }
            }
        }

        mock_requests.get(requests_mock.ANY, json=mock_response)

        self.grid.get_all_registered_nodes_ip = MagicMock(return_value=["http://this also doesnt matter"])

        response = self.grid.get_grid_hub_sessions_capacity("http://this doesnt matter")

        self.assertEqual(response, 100)

    @requests_mock.Mocker()
    def test_get_browser_usage(self, mock_requests):
        """Tests that we can figure out the usage stats for a grid"""
        mock_response = {
            "value": [
                {
                    "capabilities": {
                        "browserName": "fake_browser",
                        "browserVersion": "1"
                    }
                },
                {
                    "capabilities": {
                        "browserName": "another_fake_browser",
                        "version": "1"
                    }
                }
            ]
        }

        mock_requests.get(requests_mock.ANY, json=mock_response)

        self.grid.get_all_registered_nodes_ip = MagicMock(return_value=["http://this also doesnt matter"])

        response = self.grid.get_usage_per_browser_type("http://this doesnt matter")

        self.assertEqual(
            response,
            {
                'breakdown': {
                    u'another_fake_browser': {'version': {u'1': 1}},
                    u'fake_browser': {'version': {u'1': 1}}
                },
                'total': 2
            }
        )

    @requests_mock.Mocker()
    def test_get_browser_usage_ignores_bad(self, mock_requests):
        """Tests that malformed browsers are ignored in usage stats"""
        mock_response = {
            "value": [
                {
                    "capabilities": {
                        "browserName": "fake_browser",
                        "browserVersion": "1"
                    }
                },
                {
                    "capabilities": {
                        "browserName": "another_fake_browser",
                        "version": "1"
                    }
                },
                {
                    "capabilities": {
                        "bRoWsErNaMe": "another_fake_browser",
                        "version": "1"
                    }
                },
            ]
        }

        mock_requests.get(requests_mock.ANY, json=mock_response)

        self.grid.get_all_registered_nodes_ip = MagicMock(return_value=["http://this also doesnt matter"])

        response = self.grid.get_usage_per_browser_type("http://this doesnt matter")

        self.assertEqual(
            response,
            {
                'breakdown': {
                    u'another_fake_browser': {'version': {u'1': 1}},
                    u'fake_browser': {'version': {u'1': 1}}
                },
                'total': 2
            }
        )
