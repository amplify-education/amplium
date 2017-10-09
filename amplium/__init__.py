""" For package documentation, see README """

import logging.config

from amplium.utils import dynamodb_handler, zookeeper, datadog_handler
from amplium.config import Config

from requests import Session

from .version import __version__, __rpm_version__, __git_hash__

CONFIG = Config()
logging.config.dictConfig(CONFIG.logging)

# Create a session for connection pooling purposes
SESSION = Session()

host = CONFIG.zookeeper['host']
port = CONFIG.zookeeper['port']
nerve_directory = CONFIG.zookeeper['selenium_grid_zookeeper_path']
ZOOKEEPER = zookeeper.ZookeeperGridNodeStatus(nerve_directory, host, port)

table_name = CONFIG.dynamodb['table_name']
region = CONFIG.dynamodb['region']
DYNAMODB = dynamodb_handler.DynamoDBHandler(table_name, region)

DATADOG = datadog_handler.DatadogHandler(config=CONFIG.integrations.get('datadog'))
