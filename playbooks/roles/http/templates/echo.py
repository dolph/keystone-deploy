"""A secure echo service, protected by ``auth_token``.

When the ``auth_token`` module authenticates a request, the echo service will
respond with all the environment variables presented to it by ``auth_token``.
"""
import json

from keystoneclient.middleware import auth_token


AUTH_TOKEN_CONF = {
    'auth_protocol': 'http',
    'admin_token': 'ADMIN'}


def echo_app(environ, start_response):
    """A WSGI application that echoes the CGI environment to the user."""
    start_response('200 OK', [('Content-Type', 'application/json')])
    environment = dict((k, v) for k, v in environ.iteritems()
                       if k.startswith('HTTP_X_'))
    yield json.dumps(environment, indent=2)


app = auth_token.AuthProtocol(echo_app, AUTH_TOKEN_CONF)
