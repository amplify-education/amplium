"""Unit testing for util/zookeeper.py"""

import unittest
from amplium.utils import zookeeper
from mock import patch, MagicMock


def mock_requests_get(*args, **kwargs):
    """Mocks the requests get call"""
    if '/grid/api/proxy' in args[0] and kwargs is not None:
        json_data = {"request": {"configuration": {"maxSession": 1}}}
    else:
        json_data = {"value": [{"capabilities": {"browserName": 'test_browser', "version": '0.0.0'}}]}
    return MagicMock(status_code=200, json=MagicMock(return_value=json_data))


mock_kazoo_get = MagicMock(return_value=('{"host":"test_host","port":1234,"name":"test_node"}', ))
mock_all_registered_nodes_ip = 'amplium.utils.zookeeper.ZookeeperGridNodeStatus.get_all_registered_nodes_ip'
mock_grid_hub_session = 'amplium.utils.zookeeper.ZookeeperGridNodeStatus.get_grid_hub_sessions_capacity'
mock_get = 'amplium.utils.zookeeper.requests.get'


class ZooKeeperUnitTests(unittest.TestCase):
    """Tests for zookeeper.py"""

    @patch('amplium.utils.zookeeper.requests.get', MagicMock(side_effect=mock_requests_get))
    @patch(mock_all_registered_nodes_ip, MagicMock(return_value=['http://0:1234', 'http://1:1234']))
    def test_browser_usage(self):
        """Tests get_browser_usage function"""
        mock_zk = zookeeper.ZookeeperGridNodeStatus('test_path', 0, 1234)

        browser_data = mock_zk.get_usage_per_browser_type('test_path')

        browser_breakdown = browser_data['breakdown']
        self.assertEqual(browser_breakdown['test_browser']['version']['0.0.0'], 2)

    @patch('amplium.utils.zookeeper.requests.get')
    @patch(mock_all_registered_nodes_ip, MagicMock(return_value=['http://0:1234', 'http://1:1234']))
    def test_browser_usage_with_alt_ver(self, mock_requests):
        """Tests get_browser_usage handles alt version"""
        mock_json = {"value": [{"capabilities": {"browserName": 'test_browser', "browserVersion": '0.0.0'}}]}
        mock_response = MagicMock(status_code=200, json=MagicMock(return_value=mock_json))
        mock_requests.return_value = mock_response
        mock_zk = zookeeper.ZookeeperGridNodeStatus('test_path', 0, 1234)

        browser_data = mock_zk.get_usage_per_browser_type('test_path')

        browser_breakdown = browser_data['breakdown']
        self.assertEqual(browser_breakdown['test_browser']['version']['0.0.0'], 2)

    @patch('amplium.utils.zookeeper.requests.get')
    @patch(mock_all_registered_nodes_ip, MagicMock(return_value=['http://0:1234']))
    def test_browser_usage_no_keyerror(self, mock_requests):
        """Tests get_browser_usage handles keyerror safely"""
        mock_json = {"value": [
            {"capabilities": {"browser": 'this_shouldnt_appear', "browserVersion": '0.0.0'}},
            {"capabilities": {"browserName": 'test_browser', "browserVersion": '0.0.0'}}
        ]}
        mock_response = MagicMock(status_code=200, json=MagicMock(return_value=mock_json))
        mock_requests.return_value = mock_response
        mock_zk = zookeeper.ZookeeperGridNodeStatus('test_path', 0, 1234)

        browser_data = mock_zk.get_usage_per_browser_type('test_path')

        browser_breakdown = browser_data['breakdown']
        self.assertEqual(['test_browser'], browser_breakdown.keys())
        self.assertEqual(browser_breakdown['test_browser']['version']['0.0.0'], 1)

    @patch('amplium.utils.zookeeper.requests.get', MagicMock(side_effect=mock_requests_get))
    @patch(mock_all_registered_nodes_ip, MagicMock(return_value=['http://0:1234', 'http://1:1234']))
    def test_capacity(self):
        """Tests get_grid_hub_sessions_capacity function"""
        mock_zk = zookeeper.ZookeeperGridNodeStatus('test_path', 0, 1234)
        capacity = mock_zk.get_grid_hub_sessions_capacity('test_path')
        self.assertEqual(capacity, 2)

    @patch('kazoo.client.KazooClient.get', MagicMock(side_effect=mock_kazoo_get))
    @patch('amplium.utils.zookeeper', MagicMock())
    def test_get_node_data(self):
        """Tests if the get_node_data parses the json file given"""
        mock_zk = zookeeper.ZookeeperGridNodeStatus('test_path', 0, 1234)
        host_data = mock_zk.get_grid_node_data('test_path')
        self.assertEqual(host_data['host'], "test_host")
        self.assertEqual(host_data['port'], 1234)
        self.assertEqual(host_data['name'], 'test_node')

    @patch(mock_get, MagicMock(return_value=MagicMock(content='id : http://0:1234')))
    def test_get_all_registered_nodes_ip(self):
        """Tests the get all registered nodes ip function"""
        mock_zk = zookeeper.ZookeeperGridNodeStatus('test_path', 0, 1234)
        result = mock_zk.get_all_registered_nodes_ip('test_url')
        self.assertEqual(result[0], 'http://0:1234')

    @patch('kazoo.client.KazooClient.start', MagicMock())
    @patch('requests.get', MagicMock(side_effect=MagicMock(json={'newSessionRequestCount': 0})))
    @patch('kazoo.client.KazooClient.get_children', MagicMock(side_effect=mock_kazoo_get))
    @patch(mock_grid_hub_session, MagicMock(return_value=2))
    @patch('amplium.utils.zookeeper.ZookeeperGridNodeStatus.get_usage_per_browser_type')
    @patch('amplium.utils.zookeeper.ZookeeperGridNodeStatus.get_grid_node_data')
    def test_get_nodes(self, mock_node_data, mock_browser_usage):
        """Tests the get nodes function"""
        mock_node_data.return_value = {'host': 'test_host', 'port': 1234}
        browser_return_data = {'breakdown': {'test_browser': {'version': {'0.0.0': 1}}}, 'total': 1}
        mock_browser_usage.return_value = browser_return_data
        mock_zk = zookeeper.ZookeeperGridNodeStatus('test_path', 0, 1234)
        results = mock_zk.get_nodes()
        self.assertEqual(len(results), 1)

    @patch('kazoo.client.KazooClient.start', MagicMock())
    @patch('kazoo.client.KazooClient.get_children', MagicMock(side_effect=zookeeper.KazooTimeoutError))
    def test_get_nodes_timeout(self):
        """Tests if get nodes catches timeout error"""
        mock_zk = zookeeper.ZookeeperGridNodeStatus('test_path', 0, 1234)
        results = mock_zk.get_nodes()
        self.assertEqual(results, [])

    def test_post_session_https(self):
        """Tests the port for protocol change"""
        test_url = "https://test_host:443"
        mock_zk = zookeeper.ZookeeperGridNodeStatus('test_path', 0, 1234)
        response = mock_zk.build_url("test_host", 443)
        self.assertEqual(response, test_url)
