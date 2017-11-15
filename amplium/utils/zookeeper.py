"""Used for calling ZookeeperGridNodeStatus"""

import ast
import logging

from kazoo.client import KazooClient
from kazoo.handlers.threading import KazooTimeoutError

logger = logging.getLogger(__name__)


class ZookeeperGridNodeStatus(object):
    """Initializes the zookeeper and gets the nodes from zookeeper"""

    def __init__(self, nerve_directory, host=None, port=None):
        host = host
        port = port
        zookeeper_host = "%s:%s" % (host, port)
        self.zookeeper = KazooClient(hosts=zookeeper_host, read_only=True)
        self.nerve_directory = nerve_directory

    def get_nodes(self):
        """
        Gets the children

        Returns:
            array:   Returns an array with all the nodes with their data
        """
        try:
            self.zookeeper.start()

            children = self.zookeeper.get_children(self.nerve_directory)
            ip_addresses = [self.get_grid_node_data(child) for child in children]

            self.zookeeper.stop()

            return ip_addresses
        except KazooTimeoutError:
            logger.exception("Zookeeper Timeout Error:")
            return []

    def get_grid_node_data(self, grid_node):
        """Gets host, port, and name from the grid node"""
        child_directory = "{0}/{1}".format(self.nerve_directory, grid_node)
        child_data = self.zookeeper.get(child_directory)
        # Gets host, port, and name
        return ast.literal_eval(child_data[0])
