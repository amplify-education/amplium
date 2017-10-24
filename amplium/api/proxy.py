"""Handler for the proxying to selenium grids"""

import logging

import requests

from amplium import CONFIG, ZOOKEEPER, DYNAMODB, SESSION, DATADOG
from amplium.utils import saucelabs_handler
from amplium.api.exceptions import NoAvailableCapacityException, NoAvailableGridsException
from amplium.utils.utils import retry

logger = logging.getLogger(__name__)


def create_session(new_session):
    """Handler for creating a new session"""
    base_url = _get_base_url(new_session)

    url = '{0}/wd/hub/session'.format(base_url)
    response = send_request('POST', data=new_session, url=url)
    session_id = response.get('sessionId')

    if session_id is not None:
        # Creates a new entry into the table
        DYNAMODB.add_entry(session_id, base_url)
    return response


def delete_session(session_id):
    """Handler for deleting an existing session"""
    response = send_request('DELETE', session_id)

    # Deletes an entry
    DYNAMODB.delete_entry(session_id)

    return response


def get_command(session_id, command):
    """Handler for executing a GET command"""
    response = send_request('GET', session_id, command)
    return response


def post_command(session_id, command, command_params):
    """Handler for executing a POST command with parameters"""
    response = send_request('POST', session_id, command, command_params)
    return response


def delete_command(session_id, command):
    """Handler for executing a DELETE command"""
    response = send_request('DELETE', session_id, command)
    return response


def send_request(method, session_id=None, command=None, data=None, url=None):
    """Does request call based on command and given url"""

    if url is None:
        # Gets the address of the node based on the session id
        dynamodb_entry = DYNAMODB.get_entry(session_id)

        # Builds the url with the correct session id and the given command
        url = dynamodb_entry['BaseUrl']
        url += "/wd/hub/session/{0}".format(session_id)
        if command is not None:
            url += "/{0}".format(command)

    logger.info("%s | Sent %s request to (%s) with data: %s", session_id, method, url, data)

    try:
        # Attempts to send request to the given url
        response = SESSION.request(method=method, url=url, json=data)
        logger.info("%s | Received from (%s) with response: %s", session_id, url, response.text)
        return response.json()
    except requests.HTTPError as error:
        logger.exception("Http Error: ")
        return {'status': error.response.status_code, 'message': 'Http error occurred while proxying'},\
            error.response.status_code
    except requests.Timeout as error:
        logger.exception("Timeout Exception: ")
        return {'status': error.response.status_code, 'message': 'Timeout occurred while proxying'},\
            error.response.status_code


def _get_base_url(new_session):
    """Gets the base url based on the capabilities setting. Returns None if _get_ip_address returns None."""
    # Looks for the correct capabilities
    for key in new_session.iteritems():
        if key[0].endswith('Capabilities'):
            # If saucelabs is not used, use zookeeper to find the url
            if saucelabs_handler.is_saucelabs_requested(new_session, key[0]):
                return retry(
                    func=saucelabs_handler.get_sauce_url,
                    max_time=CONFIG.session_queue_time
                )

    ip_address = retry(
        func=_get_ip_address,
        max_time=CONFIG.session_queue_time
    )

    return ZOOKEEPER.build_url(*ip_address)


def _get_ip_address():
    """
    Gets an ip address and port number of a selenium grid hub from zookeeper.
    None is returned if no nodes were given occurs.
    """
    zookeeper_nodes = ZOOKEEPER.get_nodes()
    if not zookeeper_nodes:
        raise NoAvailableGridsException("No grids are registered to Amplium")

    nodes = sorted(
        [
            node for node in zookeeper_nodes
            if node['available_capacity'] > 0
        ],
        cmp=compare_node
    )

    if nodes:
        return nodes[0]['host'], nodes[0]['port']

    DATADOG.send(
        metric='amplium.queue_length',
        metric_type='counter',
        value=1
    )

    raise NoAvailableCapacityException("No available capacity on any grid")


def compare_node(node1, node2):
    """Sorts nodes based on lowest queue,highest total, and lowest available capacity"""
    compare_queue = node1['queue'] - node2['queue']
    if compare_queue != 0:
        return compare_queue

    compare_total = node1['total_capacity'] - node2['total_capacity']
    if compare_total != 0:
        # Note the inversion, because we want the LARGEST total capacity
        return -compare_total

    compare_available = node1['available_capacity'] - node2['available_capacity']
    return compare_available
