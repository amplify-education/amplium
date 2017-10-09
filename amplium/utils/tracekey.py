""" Module for tracekey stuff """
import uuid
import logging
import flask


def generate_tracekey(original_tracekey=None):
    """ Generate a tracekey, optionally taking in an existing tracekey to prepend to the new tracekey """
    new_tracekey = uuid.uuid1()

    if original_tracekey:
        return "{0}/{1}".format(original_tracekey, new_tracekey)

    return new_tracekey


def tracekey():
    """
    Returns the current request ID or a new one if there is none

    Prepends the client's tracekey if one is provided.
    """
    # If we've already created a tracekey, return it
    if 'tracekey' in flask.g:
        return flask.g.tracekey

    # If we haven't, generate a new one, prepending the tracekey from our client if they gave us one
    headers = flask.request.headers
    original_tracekey = headers.get("X_WGEN_TRACEKEY")
    new_tracekey = generate_tracekey(original_tracekey)

    # Store our new tracekey for future reuse
    flask.g.tracekey = new_tracekey

    return new_tracekey


class TracekeyFilter(logging.Filter):
    """ Logging filter for making the tracekey available """
    def filter(self, record):
        """ The bit that does the actual work """
        # The check for request context makes sure that we can continue to log without flask being loaded.
        record.tracekey = tracekey() if flask.has_request_context() else 'NO_TRACEKEY'
        return True
