""" Module for tracekey stuff """
import contextvars
import logging

import uuid
from aiohttp.web_middlewares import middleware

TRACE_KEY = contextvars.ContextVar('TRACE_KEY', default=None)


def generate_tracekey(original_tracekey=None):
    """Generate a tracekey, optionally taking in an existing tracekey to prepend to the new tracekey"""
    new_tracekey = uuid.uuid1()

    if original_tracekey:
        return "{0}/{1}".format(original_tracekey, new_tracekey)

    return new_tracekey


@middleware
async def trace_key_middleware(request, handler):
    """Sets the tracekey in the asyncio context if no trace key is set yet"""
    if not TRACE_KEY.get():
        original_tracekey = request.headers.get("X_WGEN_TRACEKEY")
        TRACE_KEY.set(generate_tracekey(original_tracekey))
    return await handler(request)


class TracekeyFilter(logging.Filter):
    """Logging filter for making the tracekey available"""

    def filter(self, record):
        """ The bit that does the actual work """
        # The check for request context makes sure that we can continue to log without flask being loaded.
        record.tracekey = TRACE_KEY.get() or 'NO_TRACEKEY'
        return True
