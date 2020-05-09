"""Class to get grid node data from Consul"""
import asyncio
import logging
import threading

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

    def start_listening(self):
        # Start a separate thread with a event loop so we can use consul client with asyncio
        thread = threading.Thread(target=self._run_event_loop)
        thread.start()

    def _run_event_loop(self):
        loop = asyncio.new_event_loop()
        loop.run_until_complete(self._watch())

    async def _watch(self):
        """Start polling consul for catalog updates"""
        index = None
        consul_client = consul.aio.Consul(self.host, self.port)
        logger.info('Starting to watch for changes to consul service %s', self.service_name)
        while True:
            try:
                [index, data] = await consul_client.catalog.service(self.service_name, index=index)
                logger.debug('Got grid nodes from Consul %s', data)
                nodes = []
                for node in data:
                    nodes.append(self._get_grid_node_data(node))
                logger.info('Setting grid node data %s', nodes)
                self.nodes = nodes
            except Exception:
                logger.exception('Error connecting to Consul')
                # sleep for a few seconds so we don't end up in a tight infinite loop
                await asyncio.sleep(5)

    def get_nodes(self, _: List[str] = None):
        # do nothing because the listen task will automatically restart if there are any errors
        pass

    def _get_grid_node_data(self, node: Dict) -> GridNodeData:
        return GridNodeData(
            host=node['Address'],
            port=node['ServicePort'],
            name=node['Node']
        )
