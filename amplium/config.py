"""Module for parsing Amplium's config file"""
import os
import logging
import yaml

from schema import Schema, Use, And, Optional

SCHEMA_CONFIG = Schema(
    {
        "zookeeper": {
            "host": Use(str),
            "port": And(
                Use(int),
                lambda n: 1 <= n <= 65535,
                error="Port must be an integer between 1 and 65535"
            ),
            "selenium_grid_zookeeper_path": Use(str),
        },
        "logging": {
            Optional("version", default=1): Use(int),
            Optional("disable_existing_loggers", default=True): bool,
            Optional("loggers"): {
                str: {
                    Optional("level"): Use(str),
                    Optional("handlers"): [Use(str)],
                    Optional("filters"): [Use(str)],
                    Optional("propagate"): Use(bool)
                }
            },
            Optional("handlers"): {
                str: {
                    "class": Use(str),
                    Optional("level"): Use(str),
                    Optional("formatter"): Use(str),
                    Optional("filters"): [Use(str)],
                    Optional(Use(str)): object
                }
            },
            Optional("formatters"): {
                str: {
                    Optional("format"): Use(str),
                    Optional("datefmt"): Use(str)
                }
            },
            Optional("filters"): {
                str: {
                    Optional(str): str
                }
            }
        },
        "dynamodb": {
            "table_name": Use(str),
            Optional("region", default='us-west-2'): Use(str)
        },
        Optional("integrations"): {
            Optional("saucelabs"): {
                "username": Use(str),
                "accesskey": Use(str),
            },
            Optional("datadog"): {
                "api_key": Use(str),
                "app_key": Use(str)
            }
        },
        Optional("session_queue_time", default=60 * 3): Use(int)
    },
    ignore_extra_keys=True
)

ENVVAR_CONFIG_PATH = 'AMPLIUM_CONFIG'
DEFAULT_CONFIG_PATH = '/etc/amplium/config.yml'

logger = logging.getLogger(__name__)


class Config(object):
    """Class for parsing Amplium's config file"""

    def __init__(self, config=None):
        logging.basicConfig(level=logging.DEBUG)
        config_path = os.getenv(ENVVAR_CONFIG_PATH, DEFAULT_CONFIG_PATH)

        if not config and not os.path.isfile(config_path):
            raise Exception(
                'No config provided. Please set environment variable {0} with /path/'
                'to/amplium_config.yml or use the default path: {1}'.format(
                    ENVVAR_CONFIG_PATH,
                    DEFAULT_CONFIG_PATH
                )
            )

        config = config or yaml.safe_load(open(config_path))

        self._config = self._validate_config(config)

    @property
    def zookeeper(self):
        """Dictionary containing zookeeper configuration"""
        return self._config.get('zookeeper')

    @property
    def logging(self):
        """Dictionary containing logging configuration"""
        return self._config.get('logging')

    @property
    def dynamodb(self):
        """Dictionary containing dynamodb configuration"""
        return self._config.get('dynamodb')

    @property
    def integrations(self):
        """Dictionary containing integrations configuration"""
        return self._config.get('integrations')

    @property
    def session_queue_time(self):
        """Dictionary containing integrations configuration"""
        return self._config.get('session_queue_time')

    def _validate_config(self, config):
        """Convenience function for validating a testillery config after it is parsed"""
        # Checks if integrations is included in the config
        if config.get('integrations') is None:
            config['integrations'] = {}
        return SCHEMA_CONFIG.validate(config)
