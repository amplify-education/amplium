"""Handles the SauceLabs Configurations"""
import logging

from amplium import CONFIG
from amplium.api.exceptions import IntegrationNotConfigured

logger = logging.getLogger(__name__)


def get_sauce_url():
    """Constructs the sauce url if integrations is setup correctly, otherwise return none"""
    # Creates the url based on the username and accesskey given by the config
    saucelabs_config = CONFIG.integrations.get('saucelabs')

    if not saucelabs_config:
        raise IntegrationNotConfigured("Attempted to use Saucelabs, but Saucelabs is not configured.")

    username = saucelabs_config['username']
    access_key = saucelabs_config['accesskey']
    return 'https://{0}:{1}@ondemand.saucelabs.com:443'.format(username, access_key)


def is_saucelabs_requested(session_data, capability_type):
    """Returns useSaucelabs"""
    if 'amplium:useSauceLabs' in session_data[capability_type]:
        return session_data[capability_type]['amplium:useSauceLabs']
    return False
