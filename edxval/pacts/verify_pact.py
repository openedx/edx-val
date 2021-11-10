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

    PACT_CONFIG = {
        'broker_url': settings.PACT_BROKER_BASE_URL,
        'consumer_version_selectors': [
            {'tag': 'production', 'latest': True},
            {"tag": "master", "latest": True},
        ],
        'publish_version': settings.PUBLISH_VERSION,
        'provider_tags': [settings.PUBLISH_TAGS, settings.GIT_ENV],
        'publish_verification_results': settings.PUBLISH_VERIFICATION_RESULTS,
        'headers': ['Pact-Authentication: AllowAny', ],
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
        """
        if self.PACT_CONFIG['publish_verification_results']:
            output, _ = self.verifier.verify_with_broker(
                **self.PACT_CONFIG,
                verbose=False,
                enable_pending=True,
                provider_states_setup_url=f"{self.live_server_url}{reverse('provider-state-view')}",
            )
        else:
            output, _ = self.verifier.verify_pacts(
                os.path.join(PACT_DIR, PACT_FILE),
                provider_states_setup_url=f"{self.live_server_url}{reverse('provider-state-view')}",
                headers=self.PACT_CONFIG['headers'],
            )

        assert output == 0
