""" For package documentation, see README """
import logging.config

from requests import Session
from requests.adapters import HTTPAdapter

from amplium.utils import zookeeper, datadog_handler, grid_handler, saucelabs_handler
from amplium.config import Config

from .version import __version__, __rpm_version__, __git_hash__

CONFIG = Config()
logging.config.dictConfig(CONFIG.logging)

# Create a session for connection pooling purposes
SESSION = Session()
SESSION.mount('http://', HTTPAdapter(pool_connections=100, pool_maxsize=100))
SESSION.mount('https://', HTTPAdapter(pool_connections=100, pool_maxsize=100))

host = CONFIG.zookeeper['host']
port = CONFIG.zookeeper['port']
nerve_directory = CONFIG.zookeeper['selenium_grid_zookeeper_path']
ZOOKEEPER = zookeeper.ZookeeperGridNodeStatus(nerve_directory, host, port)

DATADOG = datadog_handler.DatadogHandler(config=CONFIG.integrations.get('datadog'))

SAUCELABS = saucelabs_handler.SauceLabsHandler(config=CONFIG, session=SESSION)

GRID_HANDLER = grid_handler.GridHandler(
    config=CONFIG,
    zookeeper=ZOOKEEPER,
    datadog=DATADOG,
    saucelabs=SAUCELABS,
    session=SESSION
)
