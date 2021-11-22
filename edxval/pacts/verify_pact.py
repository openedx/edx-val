"""Pact verifier with Live server test case"""

import logging
import os

from django.conf import settings
from django.test import LiveServerTestCase
from django.urls import reverse

from pact import Verifier

log = logging.getLogger(__name__)
PACT_DIR = os.path.dirname(os.path.realpath(__file__))
PACT_FILE = "video-encode-manager-edx-val.json"


class ProviderVerificationServer(LiveServerTestCase):
    """ Execute the provider verification on the consumer pacts """

    PACT_DEFAULT_CONFIG = {
        'enable_pending': True,
        'headers': ['Pact-Authentication: AllowAny', ],
        'verbose': False,
        'publish_version': settings.PUBLISH_VERSION,
        'provider_tags': [settings.PUBLISH_TAGS, settings.GIT_ENV],
        'publish_verification_results': settings.PUBLISH_VERIFICATION_RESULTS,
        'verify_with_broker': settings.VERIFY_WITH_BROKER,
    }

    PACT_BROKER_CONFIG = {
        'broker_url': settings.PACT_BROKER_BASE_URL,
        'consumer_version_selectors': [
            {'tag': 'production', 'latest': True},
            {"tag": "master", "latest": True},
        ],
        **PACT_DEFAULT_CONFIG
    }

    @classmethod
    def setUpClass(cls):
        super().setUpClass()

        cls.verifier = Verifier(
            provider='edx-val',
            provider_base_url=cls.live_server_url,
        )

    @classmethod
    def tearDownClass(cls):
        super().tearDownClass()

    def test_verify_pact(self):
        """
        Run provider verification either using pact broker or local pact.

          * If VERIFY_WITH_BROKER environment variable is set, broker config will be used to run verification
          of pacts on broker.
          * If VERIFY_WITH_BROKER is not set, the pact specified by CHANGED_PACT_URL environment variable or the
          local directory pact will be verified. VERIFY_WITH_BROKER is not set when the contract is changed by the
          consumer and a provider verification build specific to the changed contract should be executed.
        """
        if self.PACT_DEFAULT_CONFIG['verify_with_broker']:
            output, _ = self.verifier.verify_with_broker(
                **self.PACT_BROKER_CONFIG,
                provider_states_setup_url=f"{self.live_server_url}{reverse('provider-state-view')}",
            )
        else:
            output, _ = self.verifier.verify_pacts(
                settings.CHANGED_PACT_URL or os.path.join(PACT_DIR, PACT_FILE),
                provider_states_setup_url=f"{self.live_server_url}{reverse('provider-state-view')}",
                **self.PACT_DEFAULT_CONFIG,
            )

        assert output == 0
