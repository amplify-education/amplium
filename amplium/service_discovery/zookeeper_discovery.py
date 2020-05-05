"""Used for calling ZookeeperGridNodeStatus"""
import json
import logging
from typing import List

from kazoo.client import KazooClient
from kazoo.exceptions import KazooException
from kazoo.recipe.watchers import ChildrenWatch
from kazoo.retry import KazooRetry

from amplium.models.grid_node_data import GridNodeData
from amplium.service_discovery.abstract_discovery import AbstractDiscovery

logger = logging.getLogger(__name__)


class ZookeeperGridNodeStatus(AbstractDiscovery):
    """Initializes the zookeeper and gets the nodes from zookeeper"""

    def __init__(self, nerve_directory, host=None, port=None):
        zookeeper_host = "%s:%s" % (host, port)
        connection_retry = KazooRetry(max_tries=10)
        self.zookeeper = KazooClient(hosts=zookeeper_host, read_only=True, connection_retry=connection_retry)
        self.nerve_directory = nerve_directory
        self.nodes: List[GridNodeData] = []

    def start_listening(self):
        """
        Starts the zookeeper client and sets the watcher
        """
        self.zookeeper.start()
        ChildrenWatch(self.zookeeper, self.nerve_directory, self.get_nodes)

    def get_nodes(self, children: List[str] = None):
        """
        Gets the data for the grid nodes.
        :param children: A list of Zookeeper nodes to lookup. If None, children will be looked up.
        :return: A list of tuples containing host, port, and name of each grid node.
        """
        try:
            if children is None:
                children = self.zookeeper.retry(self.zookeeper.get_children, self.nerve_directory)

            self.nodes = [self._get_grid_node_data(child) for child in children]
        except KazooException:
            logger.exception("Unable to connect to zookeeper")
            self.nodes = []
        return True

    def _get_grid_node_data(self, grid_node: str) -> GridNodeData:
        """Gets host, port, and name from the grid node"""
        child_directory = "{0}/{1}".format(self.nerve_directory, grid_node)
        child_data = self.zookeeper.retry(self.zookeeper.get, child_directory)
        # Gets host, port, and name
        data = json.loads(child_data[0])

        return GridNodeData(
            host=data.get('host'),
            port=data.get('port'),
            name=data.get('name')
        )
