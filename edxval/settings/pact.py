"""
Pact related Django settings.

Making a separate setting file for pact so that the configuration
does not cause issue with regular unit testing.
"""
import os

from edxval.settings.test import *  # pylint: disable=wildcard-import

PUBLISH_VERIFICATION_RESULTS = os.environ.get('PUBLISH_VERIFICATION_RESULTS', 'False').lower() in ('true', 'yes', '1')
PROVIDER_STATES_SETUP_VIEW_URL = True
PACT_BROKER_BASE_URL = os.environ.get('PACT_BROKER_BASE_URL', 'http://localhost:9292')
PUBLISH_VERSION = os.environ.get('PUBLISH_VERSION', '1')
PUBLISH_TAGS = os.environ.get('PUBLISH_TAGS', 'master')
PUBLISH_TAGS = [PUBLISH_TAGS, 'production' if PUBLISH_TAGS == 'master' else 'development']

MIDDLEWARE = MIDDLEWARE + ('edxval.pacts.middleware.AuthenticationMiddleware',)
