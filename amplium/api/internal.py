"""Root handler for the API"""
import logging
from amplium import ZOOKEEPER

logger = logging.getLogger(__name__)


def get_status():
    """Handler for the status path"""
    nodes = ZOOKEEPER.get_nodes()
    data_packet = {"status": "OK", "nodes": nodes}
    return data_packet
