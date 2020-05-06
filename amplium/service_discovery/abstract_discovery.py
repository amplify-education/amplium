"""Base class that different service discovery strategies will extend"""
from abc import ABC, abstractmethod

from typing import List

from amplium.models.grid_node_data import GridNodeData


class AbstractDiscovery(ABC):
    """Base class that different service discovery strategies will extend"""
    nodes: List[GridNodeData]

    @abstractmethod
    def get_nodes(self, children: List[str] = None):
        """Force a update of the local nodes cache"""

    @abstractmethod
    def start_listening(self):
        """Start polling the backend for node data"""
