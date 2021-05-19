"""Class to get grid node data from Consul"""
import logging

import threading
from time import sleep
from typing import Dict, List
import consul.aio

from amplium.models.grid_node_data import GridNodeData
from amplium.service_discovery.abstract_discovery import AbstractDiscovery

logger = logging.getLogger(__name__)


class ConsulGridNodeStatus(AbstractDiscovery):
    """Class to get grid node data from Consul"""

    def __init__(self, service_name, host, port):
        self.host = host
        self.port = port
        self.service_name = service_name
        self.nodes = []
        self.consul = consul.Consul(self.host, self.port)

    def start_listening(self):
        # Start a watch in a separate thread because it loops forever
        thread = threading.Thread(target=self._watch)
        thread.start()

    def _watch(self):
        """Start polling consul for catalog updates"""
        index = None
        logger.info('Starting to watch for changes to consul service %s', self.service_name)
        while True:
            try:
                index, data = self.consul.catalog.service(
                    self.service_name,
                    index=index,
                    filter="NodeMeta.is_testing!=1"
                )
                logger.debug('Got grid nodes from Consul %s', data)
                nodes = []
                for node in data:
                    # Consul will return services even if their underlying nodes are failing checks
                    # we noticed that the selenium grid nodes sometimes pass service checks despite
                    # the nodes being unhealthy
                    # so query consul to confirm that the node is healthy
                    if self._is_node_healthy(node['Node']):
                        nodes.append(self._get_grid_node_data(node))
                logger.info('Setting grid node data %s', nodes)
                self.nodes = nodes
            except Exception:
                logger.exception('Error connecting to Consul')
                # sleep for a few seconds so we don't end up in a tight infinite loop
                sleep(5)

    def _is_node_healthy(self, node: str):
        _, node_health_checks = self.consul.health.node(node)
        for check in node_health_checks:
            if check['Status'] != 'passing':
                return False
        return True

    def get_nodes(self, _: List[str] = None):
        # do nothing because the listen task will automatically restart if there are any errors
        pass

    def _get_grid_node_data(self, node: Dict) -> GridNodeData:
        return GridNodeData(
            host=node['Address'],
            port=node['ServicePort'],
            name=node['Node']
        )
