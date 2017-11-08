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

    @patch('kazoo.client.KazooClient.get', MagicMock(side_effect=mock_kazoo_get))
    @patch('amplium.utils.zookeeper', MagicMock())
    def test_get_node_data(self):
        """Tests if the get_node_data parses the json file given"""
        mock_zk = zookeeper.ZookeeperGridNodeStatus('test_path', 0, 1234)
        host_data = mock_zk.get_grid_node_data('test_path')
        self.assertEqual(host_data['host'], "test_host")
        self.assertEqual(host_data['port'], 1234)
        self.assertEqual(host_data['name'], 'test_node')

    @patch('kazoo.client.KazooClient.start', MagicMock())
    @patch('kazoo.client.KazooClient.get_children', MagicMock(side_effect=zookeeper.KazooTimeoutError))
    def test_get_nodes_timeout(self):
        """Tests if get nodes catches timeout error"""
        mock_zk = zookeeper.ZookeeperGridNodeStatus('test_path', 0, 1234)
        results = mock_zk.get_nodes()
        self.assertEqual(results, [])

    @patch('kazoo.client.KazooClient.start', MagicMock())
    @patch('kazoo.client.KazooClient.get_children', MagicMock(return_value=["node1"]))
    @patch('kazoo.client.KazooClient.get', MagicMock(side_effect=[("{'host': 'node1', 'port': 123}", None)]))
    def test_get_nodes(self):
        """Tests that we can get nodes"""
        mock_zk = zookeeper.ZookeeperGridNodeStatus('test_path', 0, 1234)

        response = mock_zk.get_nodes()

        self.assertEquals(response, [{'host': 'node1', 'port': 123}])
