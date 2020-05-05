"""Class to get grid node data from Consul"""
import logging
from typing import Dict, List

import consul.aio

from amplium.models.grid_node_data import GridNodeData
from amplium.service_discovery.abstract_discovery import AbstractDiscovery

logger = logging.getLogger(__name__)


class ConsulGridNodeStatus(AbstractDiscovery):
    """Class to get grid node data from Consul"""
    def __init__(self, service_name, host, port):
        self.consul = consul.aio.Consul(host, port)
        self.service_name = service_name
        self.nodes = []

    async def start_listening(self):
        """Start polling consul for catalog updates"""
        try:
            index = None
            while True:
                [index, data] = await self.consul.catalog.service(self.service_name, index=index)
                nodes = []
                for node in data:
                    nodes.append(self._get_grid_node_data(node))
                self.nodes = nodes
        except Exception:
            logger.exception('Exception while getting grid node data from consul')

    def get_nodes(self, _: List[str] = None):
        data = self.consul.catalog.service(self.service_name)
        nodes = []
        for node in data:
            nodes.append(self._get_grid_node_data(node))
        self.nodes = nodes

    def _get_grid_node_data(self, node: Dict) -> GridNodeData:
        return GridNodeData(
            host=node['Address'],
            port=node['ServicePort'],
            name=node['Node']
        )
