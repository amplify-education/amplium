"""Handler for the proxying to selenium grids"""

import logging

import requests

from amplium import SESSION, GRID_HANDLER

logger = logging.getLogger(__name__)


def create_session(new_session):
    """Handler for creating a new session"""
    grid_url = GRID_HANDLER.get_base_url(new_session)

    url = '{0}/wd/hub/session'.format(grid_url)
    response = send_request('POST', data=new_session, url=url)
    session_id = response.get('sessionId')

    if session_id is not None:
        response['sessionId'] = GRID_HANDLER.generate_session_id(session_id, grid_url)
    return response


def delete_session(session_id):
    """Handler for deleting an existing session"""
    response = send_request('DELETE', session_id)
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
        session_id, url = GRID_HANDLER.unroll_session_id(session_id)
        url += "/wd/hub/session/{0}".format(session_id)
        if command is not None:
            url += "/{0}".format(command)

    logger.info("%s | Sent %s request to (%s) with data: %s", session_id, method, url, data)

    try:
        # Attempts to send request to the given url
        response = SESSION.request(method=method, url=url, json=data)
        logger.info("%s | Received from (%s) with response: %s", session_id, url, response.text)
        return response.json()
    except (requests.HTTPError, requests.Timeout, requests.ConnectionError) as error:
        logger.exception("Error while handling request")
        return (
            {'status': error.response.status_code, 'message': 'Error occurred while proxying'},
            error.response.status_code
        )
