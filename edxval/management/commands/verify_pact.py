"""
Management command to verify VEM pact.
"""

import logging

from django.conf import settings
from django.core.management.base import BaseCommand

from pact import Verifier

log = logging.getLogger(__name__)


class Command(BaseCommand):
    """
    Management command to verify VAL provider pacts.

    Example Usage:  python manage.py verify_pact --settings=edxval.settings.test
    It should be run explicitly with test or test-only settings because the pact verification requires
    some database operations that should not occur in a production related database.
    """
    help = "Verify the VAL provider pacts"

    default_opts = {
            'broker_url': getattr(settings, 'PACT_BROKER_BASE_URL', None),
            'publish_version': '1',
            'publish_verification_results': getattr(settings, 'PUBLISH_VERIFICATION_RESULTS', False)
        }

    def verify_pact(self):
        """
        Verify the pacts with Pact-verifier.
        """
        verifier = Verifier(
            provider='VAL',
            provider_base_url=settings.PROVIDER_BASE_URL
        )

        if self.default_opts['broker_url']:
            verifier.verify_with_broker(
                **self.default_opts,
                verbose=False,
                provider_states_setup_url=settings.PROVIDER_STATES_URL,
            )
        else:
            verifier.verify_pacts(
                'edxval/pacts/vem-val.json',
                provider_states_setup_url=settings.PROVIDER_STATES_URL,
            )

    def handle(self, *args, **options):
        log.info("Starting pact verification")
        self.verify_pact()
        log.info('Pact verification completed')
