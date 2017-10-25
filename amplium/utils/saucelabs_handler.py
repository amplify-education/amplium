"""Handles the SauceLabs Configurations"""
import logging

from requests import Session

from amplium import CONFIG
from amplium.api.exceptions import IntegrationNotConfigured, NoAvailableCapacityException, AmpliumException

logger = logging.getLogger(__name__)
session = Session()


def get_sauce_url():
    """Constructs the sauce url if integrations is setup correctly, otherwise return none"""
    # Creates the url based on the username and accesskey given by the config
    saucelabs_config = CONFIG.integrations.get('saucelabs')

    if not saucelabs_config:
        raise IntegrationNotConfigured("Attempted to use SauceLabs, but SauceLabs is not configured.")

    username = saucelabs_config['username']
    access_key = saucelabs_config['accesskey']

    if is_saucelabs_available():
        return 'https://{0}:{1}@ondemand.saucelabs.com:443'.format(username, access_key)
    else:
        raise NoAvailableCapacityException("SauceLabs has no available capacity.")


def is_saucelabs_requested(session_data, capability_type):
    """Returns useSaucelabs"""
    if 'amplium:useSauceLabs' in session_data[capability_type]:
        return session_data[capability_type]['amplium:useSauceLabs']
    return False


def is_saucelabs_available():
    """
    Convenience function for checking whether SauceLabs has available capacity.
    :return: True if SauceLabs has available capacity, false otherwise.
    """
    saucelabs_config = CONFIG.integrations.get('saucelabs')
    username = saucelabs_config['username']
    access_key = saucelabs_config['accesskey']
    session.auth = (username, access_key)

    response = session.get(
        "https://saucelabs.com/rest/v1.1/users/{username}/concurrency".format(username=username)
    )

    if response.status_code == 401:
        raise AmpliumException(
            message="SauceLabs integration is not correctly configured: Invalid credentials",
            error="AMPLIUM_SAUCELABS_CREDENTIALS_BAD",
            status_code=500
        )
    elif response.status_code != 200:
        raise AmpliumException(
            message="Error communicating with SauceLabs",
            error="AMPLIUM_SAUCELABS_ERROR",
            status_code=500
        )

    response_json = response.json()

    limits = response_json["concurrency"]["ancestor"]["allowed"]
    usages = response_json["concurrency"]["ancestor"]["current"]

    limit = limits.get("mac") or limits.get("real_device", 0)
    usage = usages.get("mac") or usages.get("real_device", 0)

    return bool(limit - usage)
