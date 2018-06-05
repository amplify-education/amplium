"""Used for calling ZookeeperGridNodeStatus"""
import ast
import logging

from kazoo.client import KazooClient
from kazoo.exceptions import KazooException
from kazoo.recipe.watchers import ChildrenWatch

logger = logging.getLogger(__name__)


class ZookeeperGridNodeStatus(object):
    """Initializes the zookeeper and gets the nodes from zookeeper"""

    def __init__(self, nerve_directory, host=None, port=None):
        host = host
        port = port
        zookeeper_host = "%s:%s" % (host, port)
        self.zookeeper = KazooClient(hosts=zookeeper_host, read_only=True)
        self.nerve_directory = nerve_directory
        self.nodes = []

    def start_listening(self):
        """
        Starts the zookeeper client and sets the watcher
        """
        self.zookeeper.start()
        ChildrenWatch(self.zookeeper, self.nerve_directory, self.get_nodes)

    def get_nodes(self, children):
        """
        Gets the data for the grid nodes.
        :param children: A list of Zookeeper nodes to lookup.
        :return: A list of tuples containing host, port, and name of each grid node.
        """
        try:
            self.nodes = [self.get_grid_node_data(child) for child in children]
        except KazooException:
            logger.exception("Unable to connect to zookeeper")
            self.nodes = []
        return True

    def get_grid_node_data(self, grid_node):
        """Gets host, port, and name from the grid node"""
        child_directory = "{0}/{1}".format(self.nerve_directory, grid_node)
        child_data = self.zookeeper.retry(self.zookeeper.get, child_directory)
        # Gets host, port, and name
        return ast.literal_eval(child_data[0])
