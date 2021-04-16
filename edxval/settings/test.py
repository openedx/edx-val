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
