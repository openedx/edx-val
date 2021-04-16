"""
Test only settings.
"""
from edxval.settings.base import *  # pylint: disable=wildcard-import

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',  # Add 'postgresql_psycopg2', 'mysql', 'sqlite3' or 'oracle'.
        'NAME': 'video.test.db',                      # Or path to database file if using sqlite3.
        'USER': '',                      # Not used with sqlite3.
        'PASSWORD': '',                  # Not used with sqlite3.
        'HOST': '',                      # Set to empty string for localhost. Not used with sqlite3.
        'PORT': '',                      # Set to empty string for default. Not used with sqlite3.
    }
}

TEST_ONLY_URLS = True
PROVIDER_BASE_URL = 'http://127.0.0.1:8000'
PROVIDER_STATES_URL = '{}/edxval/pact/provider_states/'.format(PROVIDER_BASE_URL)

# PACT BROKER

# if env variables are in place
# import os
# PACT_BROKER_BASE_URL = os.environ.get('PACT_BROKER_BASE_URL', None)
# PACT_BROKER_BASE_URL = os.environ.get('PUBLISH_VERIFICATION_RESULTS', False)

PACT_BROKER_BASE_URL = 'http://localhost:9292'
PUBLISH_VERIFICATION_RESULTS = True

JWT_AUTH = {
    'JWT_AUDIENCE': 'test-aud',
    'JWT_DECODE_HANDLER': 'edx_rest_framework_extensions.auth.jwt.decoder.jwt_decode_handler',
    'JWT_ISSUER': 'test-iss',
    'JWT_LEEWAY': 1,
    'JWT_SECRET_KEY': 'test-key',
    'JWT_ALGORITHM': 'HS256',
    'JWT_SUPPORTED_VERSION': '1.0.0',
    'JWT_VERIFY_AUDIENCE': True,
    'JWT_VERIFY_EXPIRATION': True,
    'JWT_AUTH_HEADER_PREFIX': 'JWT',
    'JWT_ISSUERS': [
        {
            'ISSUER': 'test-issuer-1',
            'SECRET_KEY': 'test-secret-key',
            'AUDIENCE': 'test-audience',
        }
    ],
}

MIDDLEWARE = list(MIDDLEWARE) + ['edxval.pacts.middleware.AuthenticationMiddleware']
MIDDLEWARE = tuple(MIDDLEWARE)
