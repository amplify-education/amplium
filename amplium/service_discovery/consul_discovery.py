"""Class to get grid node data from Consul"""
import asyncio
import logging
from time import sleep

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

    def start_listening(self):
        task = asyncio.create_task(self._listen())

        # the task is never supposed to finish because it does "while True"
        # if it does finish due to an exception then start it again
        task.add_done_callback(self.start_listening)

    async def _listen(self):
        """Start polling consul for catalog updates"""
        logger.info('Starting to watch for changes to consul service %s', self.service_name)
        try:
            index = None
            while True:
                [index, data] = await self.consul.catalog.service(self.service_name, index=index)
                logger.info('Got grid nodes from Consul %s', data)
                nodes = []
                for node in data:
                    nodes.append(self._get_grid_node_data(node))
                logger.info('Setting grid node data %s', nodes)
                self.nodes = nodes
        except Exception:
            logger.exception('Error connecting to Consul')

            # The task will be automatically restarted if it fails
            # sleep for a few seconds so we don't end up in a tight infinite loop
            await sleep(10)

    def get_nodes(self, _: List[str] = None):
        # do nothing because the listen task will automatically restart if there are any errors
        pass

    def _get_grid_node_data(self, node: Dict) -> GridNodeData:
        return GridNodeData(
            host=node['Address'],
            port=node['ServicePort'],
            name=node['Node']
        )
