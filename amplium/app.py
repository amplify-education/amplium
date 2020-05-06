""" Run of the Amplium application """

import connexion
from aiohttp.web_middlewares import middleware

from amplium import DISCOVERY
from amplium.api.exception_handlers import handle_amplium_exception, handle_unknown_exception
from amplium.api.exceptions import AmpliumException
from amplium.utils.tracekey import trace_key_middleware


@middleware
async def error_handler_middleware(request, handler):
    """Handle errors thrown while processing a request"""
    try:
        response = await handler(request)
        return response
    except AmpliumException as ex:
        return handle_amplium_exception(ex)
    except Exception as ex:
        return handle_unknown_exception(ex)


# Create connexion app and add the API
app = connexion.AioHttpApp(
    __name__,
    specification_dir='./specs/'
)
app._only_one_api = True
app.add_api(
    'swagger.yml',
    arguments={'title': 'Amplium API'}
)

# Expose application var for WSGI support
application = app.app

# Append error handling middleware
application.middlewares.append(error_handler_middleware)

# Append trace key middle
application.middlewares.append(trace_key_middleware)


async def start_listener(*_):
    """
    Wrap the discovery method start_listening function in a async wrapper so it can be run as a task
    during application startup
    """
    DISCOVERY.start_listening()


if __name__ == '__main__':
    application.on_startup.append(start_listener)

    app.run(
        port=8081,
        debug=True
    )
