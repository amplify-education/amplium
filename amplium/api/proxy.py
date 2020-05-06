"""Handler for the proxying to selenium grids"""
import json
import logging
from typing import Tuple, Dict

from aiohttp.web_response import json_response
from aiohttp.web import Response

import requests

from amplium import SESSION, GRID_HANDLER

logger = logging.getLogger(__name__)


def create_session(new_session):
    """Handler for creating a new session"""
    grid_url = GRID_HANDLER.get_base_url(new_session)

    url = '{0}/wd/hub/session'.format(grid_url)
    response, status = send_request('POST', data=new_session, url=url)
    session_id = response.get('sessionId')

    if session_id is not None:
        response['sessionId'] = GRID_HANDLER.generate_session_id(session_id, grid_url)
    return json_response(
        data=response,
        status=status
    )


def delete_session(session_id):
    """Handler for deleting an existing session"""
    response, status = send_request('DELETE', session_id)
    return json_response(
        data=response,
        status=status
    )


def get_command(session_id, command):
    """Handler for executing a GET command"""
    response, status = send_request('GET', session_id, command)
    return json_response(
        data=response,
        status=status
    )


def post_command(session_id, command, command_params):
    """Handler for executing a POST command with parameters"""
    response, status = send_request('POST', session_id, command, command_params)
    return json_response(
        data=response,
        status=status
    )


def delete_command(session_id, command):
    """Handler for executing a DELETE command"""
    response, status = send_request('DELETE', session_id, command)
    return json_response(
        data=response,
        status=status
    )


def get_session_info(session_id):
    """Retrieve an info about a specific session by executing
    GET /grid/api/testsession?session={session_id}
    returns: dict()
    Example of return data:
    {
        "inactivityTime": 258610,
        "internalKey": "86723674-e6c4-4c0b-84e1-9d9b59250134",
        "msg": "slot found !",
        "proxyId": "http://10.101.9.142:5555",
        "session": "6df13e64df39c3d21f65380a0af04213",
        "success": true
    }
    """
    session_id, url_ = GRID_HANDLER.unroll_session_id(session_id)
    url_ = "{}/grid/api/testsession?session={}".format(url_, session_id)
    response, status = send_request('GET', session_id, url=url_)
    return Response(
        body=json.dumps(response),
        status=status
    )


def send_request(method, session_id=None, command=None, data=None, url=None) -> Tuple[Dict, int]:
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
        return response.json(), 200
    except (requests.HTTPError, requests.Timeout, requests.ConnectionError) as error:
        logger.exception("Error while handling request")
        return (
            {'status': error.response.status_code, 'message': 'Error occurred while proxying'},
            error.response.status_code
        )
