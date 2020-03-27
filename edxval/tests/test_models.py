# -*- coding: utf-8 -*-
""" Test for models """
from __future__ import absolute_import

from cryptography.fernet import InvalidToken
from django.test import TestCase, override_settings

from edxval.models import TranscriptCredentials, TranscriptProviderType, Video, VideoTranscript
from edxval.tests import constants
from edxval.utils import invalidate_fernet_cached_properties


class VideoTranscriptTest(TestCase):
    """
    Test VideoTranscript model
    """

    def setUp(self):
        """
        Creates Profile objects and a video object
        """
        self.transcript_data = constants.VIDEO_TRANSCRIPT_CIELO24
        super(VideoTranscriptTest, self).setUp()

    def test_filename_property_new_line(self):
        """
        Test that filename does not contain any "\n".
        New line is not permmited in response headers.
        """
        video = Video.objects.create(**constants.VIDEO_DICT_NEW_LINE)
        video_trancript = VideoTranscript.objects.create(
            video=video,
            language_code=self.transcript_data['language_code'],
            file_format=self.transcript_data['file_format'],
            provider=self.transcript_data['provider'],
        )

        self.assertNotIn('\n', video_trancript.filename)
        assert str(video_trancript) == "en Transcript for new-line-not-allowed"


class TranscriptCredentialsTest(TestCase):
    """
    Test suite for TranscriptCredentials model.
    """
    def setUp(self):
        super(TranscriptCredentialsTest, self).setUp()
        self.credentials_data = {
            'org': 'MAx',
            'provider': TranscriptProviderType.CIELO24,
            'api_key': 'test-key',
            'api_secret': 'test-secret'
        }
        TranscriptCredentials.objects.create(**self.credentials_data)

    def test_decryption(self):
        """
        Verify that with unchanged encryption key, the decrypted data will be same as before encryption.
        """
        credentials = TranscriptCredentials.objects.get(
            org=self.credentials_data['org'], provider=self.credentials_data['provider']
        )
        self.assertEqual(credentials.api_key, self.credentials_data['api_key'])
        self.assertEqual(credentials.api_secret, self.credentials_data['api_secret'])

    def test_decryption_with_new_key(self):
        """
        Verify that with a new encryption key, previously encrypted data cannot be decrypted.
        """
        invalidate_fernet_cached_properties(TranscriptCredentials, ['api_key', 'api_secret'])
        with override_settings(FERNET_KEYS=['new-key']):
            with self.assertRaises(InvalidToken):
                TranscriptCredentials.objects.get(
                    org=self.credentials_data['org'], provider=self.credentials_data['provider']
                )
