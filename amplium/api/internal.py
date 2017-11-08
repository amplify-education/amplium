"""Root handler for the API"""
import logging

from amplium import GRID_HANDLER

logger = logging.getLogger(__name__)


def get_status():
    """Handler for the status path"""
    data = GRID_HANDLER.get_grid_info()
    data_packet = {"status": "OK", "nodes": data}
    return data_packet
