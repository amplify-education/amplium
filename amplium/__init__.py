""" For package documentation, see README """
import logging.config

from requests import Session
from requests.adapters import HTTPAdapter

from amplium.config import Config
from amplium.service_discovery.abstract_discovery import AbstractDiscovery
from amplium.service_discovery.consul_discovery import ConsulGridNodeStatus
from amplium.service_discovery.zookeeper_discovery import ZookeeperGridNodeStatus
from amplium.utils import datadog_handler, grid_handler, saucelabs_handler
from .version import __version__, __rpm_version__, __git_hash__

CONFIG = Config()
logging.config.dictConfig(CONFIG.logging)

# Create a session for connection pooling purposes
SESSION = Session()
SESSION.mount('http://', HTTPAdapter(pool_connections=100, pool_maxsize=100))
SESSION.mount('https://', HTTPAdapter(pool_connections=100, pool_maxsize=100))

DISCOVERY: AbstractDiscovery  # Needed to make mypy be happy

if CONFIG.zookeeper:
    host = CONFIG.zookeeper['host']
    port = CONFIG.zookeeper['port']
    nerve_directory = CONFIG.zookeeper['selenium_grid_zookeeper_path']
    DISCOVERY = ZookeeperGridNodeStatus(nerve_directory, host, port)
elif CONFIG.consul:
    host = CONFIG.consul['host']
    port = CONFIG.consul['port']
    service_name = CONFIG.consul['selenium_grid_service_name']
    DISCOVERY = ConsulGridNodeStatus(service_name, host, port)
else:
    raise Exception('Zookeeper or Consul configuration is required')

DATADOG = datadog_handler.DatadogHandler(config=CONFIG.integrations.get('datadog'))

SAUCELABS = saucelabs_handler.SauceLabsHandler(config=CONFIG, session=SESSION)

GRID_HANDLER = grid_handler.GridHandler(
    config=CONFIG,
    discovery=DISCOVERY,
    datadog=DATADOG,
    saucelabs=SAUCELABS,
    session=SESSION
)
