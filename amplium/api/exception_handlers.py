"""Contains exception handlers for Flask/Connexion"""
import json
import logging

from flask import Response


logger = logging.getLogger(__name__)


# pylint: disable=unused-argument
def handle_unknown_exception(exception):
    """
    Returns a generic response for any unhandled exceptions
    :param exception: The exception to handle.
    :return: A generic 500 response.
    """
    logger.exception("Unknown exception encountered:")
    return Response(
        response=json.dumps(
            {
                "value": "Amplium exception: %s" % str(exception),
                "status": "ERROR"
            }
        ),
        status=500,
        mimetype="application/json"
    )


def handle_amplium_exception(exception):
    """
    Returns a custom response for any unhandled Amplium exceptions
    :param exception: The exception to handle. Must be subclassed from AmpliumException.
    :return: An appropriate error response.
    """
    logger.exception("Amplium exception encountered:")
    return Response(
        response=json.dumps(
            {
                "value": exception.error,
                "status": "ERROR"
            }
        ),
        status=exception.status_code,
        mimetype="application/json"
    )
