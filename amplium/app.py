""" Run of the Amplium application """
import asyncio

import connexion
from aiohttp.web_middlewares import middleware

from amplium import DISCOVERY, ConsulGridNodeStatus, ZookeeperGridNodeStatus
from amplium.api.exception_handlers import handle_amplium_exception, handle_unknown_exception
from amplium.api.exceptions import AmpliumException


@middleware
async def error_handler(request, handler):
    """Handle errors thrown while processing a request"""
    try:
        return await handler(request)
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
application.middlewares.append(error_handler)

loop = asyncio.get_event_loop()
if __name__ == '__main__':
    if isinstance(DISCOVERY, ConsulGridNodeStatus):
        consul_discovery: ConsulGridNodeStatus = DISCOVERY
        application['dispatch'] = loop.create_task(consul_discovery.start_listening())
    elif isinstance(DISCOVERY, ZookeeperGridNodeStatus):
        zookeeper_discovery: ZookeeperGridNodeStatus = DISCOVERY
        zookeeper_discovery.start_listening()
    else:
        raise Exception('Invalid Service Discovery Class')

    app.run(
        port=8081,
        debug=True
    )
