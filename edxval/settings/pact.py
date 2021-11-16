"""
Pact related Django settings.

Making a separate setting file for pact so that the configuration
does not cause issue with regular unit testing.
"""
import os

from edxval.settings.test import *  # pylint: disable=wildcard-import

CHANGED_PACT_URL = os.environ.get('CHANGED_PACT_URL')
GIT_ENV = os.environ.get('GIT_ENV', 'development')
PROVIDER_STATES_SETUP_VIEW_URL = True
PACT_BROKER_BASE_URL = os.environ.get('PACT_BROKER_BASE_URL', 'http://localhost:9292')
PUBLISH_TAGS = os.environ.get('PUBLISH_TAGS', 'master')
PUBLISH_VERSION = os.environ.get('PUBLISH_VERSION', '1')
PUBLISH_VERIFICATION_RESULTS = os.environ.get('PUBLISH_VERIFICATION_RESULTS', 'False').lower() in ('true', 'yes', '1')

# By default, the verification will be done from broker. This option will need to be
# overridden when doing verification for a changed contract
VERIFY_WITH_BROKER = os.environ.get('VERIFY_WITH_BROKER', 'True').lower() in ('true', 'yes', '1')

MIDDLEWARE = MIDDLEWARE + ('edxval.pacts.middleware.AuthenticationMiddleware',)
