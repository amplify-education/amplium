"""Handler for interacting with Datadog"""
import logging
import time
import uuid

from datadog import initialize, api
from datadog.api.exceptions import (
    ClientError,
    HttpTimeout,
    HttpBackoff,
    HTTPError,
    ApiError,
    ApiNotInitialized
)


logger = logging.getLogger(__name__)


class DatadogHandler(object):
    """Handler for interacting with Datadog"""

    def __init__(self, config):
        self.identifier = str(uuid.uuid1())

        # Initialize the datadog API if it was configured
        if config:
            initialize(**config)

    def send(self, metric, value, metric_type, tags=None):
        """
        Convenience function for sending a metric to Datadog and logging any errors that are returned.
        :param metric: An unique identifier for the metric.
        :param value: The value of the metric
        :param metric_type: The type of the metric. One of ['gauge', 'counter']
        :param tags: List of strings representing tags that should be applied to the metric.
        """
        try:
            api.Metric.send(
                metric=metric,
                type=metric_type,
                points=(time.time(), value),
                host=self.identifier,
                tags=tags
            )
        except ApiNotInitialized:
            logger.debug("Attempted to send Datadog metric, but Datadog is not initialized.", exc_info=True)
        except (ClientError, HttpBackoff, HTTPError, HttpTimeout, ApiError):
            logger.warning("Datadog encountered an error", exc_info=True)
