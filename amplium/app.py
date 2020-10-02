""" Run of the Amplium application """
import os
os.environ['DD_SERVICE'] = 'mhcamplium'

# Import ddtrace after setting service name so that it picks up the correct name
# pylint: disable=wrong-import-position
from ddtrace import patch_all
patch_all(logging=True)

import connexion

from amplium import DISCOVERY
from amplium.api.exception_handlers import handle_amplium_exception, handle_unknown_exception
from amplium.api.exceptions import AmpliumException

# Create connexion app and add the API
app = connexion.App(
    __name__,
    specification_dir='./specs/'
)
app.add_api(
    'swagger.yml',
    arguments={'title': 'Amplium API'}
)

app.add_error_handler(AmpliumException, handle_amplium_exception)
app.add_error_handler(Exception, handle_unknown_exception)
app.app.before_first_request(DISCOVERY.start_listening)

# Expose application var for WSGI support
application = app.app

if __name__ == '__main__':
    app.run(
        port=8081,
        debug=True
    )
