"""Root handler for the API"""
import logging
from aiohttp.web_response import json_response

from amplium import GRID_HANDLER

logger = logging.getLogger(__name__)


def get_status():
    """Handler for the status path"""
    data = GRID_HANDLER.get_grid_info()
    data_packet = {"status": "OK", "nodes": data}
    status_code = 200 if data else 503
    return json_response(
        data=data_packet,
        status=status_code
    )
