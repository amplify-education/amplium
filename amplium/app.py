""" Run of the Amplium application """

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

# Expose application var for WSGI support
application = app.app

if __name__ == '__main__':
    DISCOVERY.start_listening()
    app.run(
        port=8081,
        debug=True
    )
