# -*- coding: utf-8 -*-
"""
Tests for transcript utils.
"""
from __future__ import absolute_import

import json
import textwrap

import responses
from ddt import data, ddt, unpack
from django.test import TestCase
from mock import patch
from rest_framework import status

from edxval.enum import TranscriptionProviderErrorType
from edxval.exceptions import TranscriptsGenerationException
from edxval.models import TranscriptProviderType
from edxval.transcript_utils import Transcript, validate_transcript_credentials


@ddt
class TestTranscriptUtils(TestCase):
    """
    Tests transcripts conversion util.
    """
    def setUp(self):
        super(TestTranscriptUtils, self).setUp()

        self.srt_transcript = textwrap.dedent(u"""\
            0
            00:00:10,500 --> 00:00:13,000
            Elephant&#39;s Dream 大象的梦想

            1
            00:00:15,000 --> 00:00:18,000
            At the left we can see...

        """).encode('utf8')

        self.sjson_transcript = textwrap.dedent(u"""\
            {
                "start": [
                    10500,
                    15000
                ],
                "end": [
                    13000,
                    18000
                ],
                "text": [
                    "Elephant&#39;s Dream 大象的梦想",
                    "At the left we can see..."
                ]
            }
        """).encode('utf8')

    @data(
        ('invalid_input_format', 'sjson'),
        ('sjson', 'invalid_output_format'),
        ('invalid_input_format', 'invalid_output_format')
    )
    @unpack
    def test_invalid_transcript_format(self, input_format, output_format):
        """
        Tests that transcript conversion raises `AssertionError` on invalid input/output formats.
        """
        with self.assertRaises(AssertionError):
            Transcript.convert(self.sjson_transcript, input_format, output_format)

    def test_convert_srt_to_srt(self):
        """
        Tests that srt to srt conversion works as expected.
        """
        expected = self.srt_transcript.decode('utf-8')
        actual = Transcript.convert(self.srt_transcript, 'srt', 'srt')
        self.assertEqual(actual, expected)

    def test_convert_sjson_to_srt(self):
        """
        Tests that the sjson transcript is successfully converted into srt format.
        """
        expected = self.srt_transcript.decode('utf-8')
        actual = Transcript.convert(self.sjson_transcript, 'sjson', 'srt')
        self.assertEqual(actual, expected)

    def test_convert_srt_to_sjson(self):
        """
        Tests that the srt transcript is successfully converted into sjson format.
        """
        expected = self.sjson_transcript.decode('utf-8')
        actual = Transcript.convert(self.srt_transcript, 'srt', 'sjson')
        self.assertDictEqual(json.loads(actual), json.loads(expected))

    def test_convert_invalid_srt_to_sjson(self):
        """
        Tests that TranscriptsGenerationException was raises on trying
        to convert invalid srt transcript to sjson.
        """
        invalid_srt_transcript = b'invalid SubRip file content'
        with self.assertRaises(TranscriptsGenerationException):
            Transcript.convert(invalid_srt_transcript, 'srt', 'sjson')


@ddt
class TestCredentialsUtils(TestCase):
    """
    Test Suite for various transcript credential utilities.
    """

    CIELO24_LOGIN_URL = "https://sandbox.cielo24.com/api/account/login"

    @patch('edxval.transcript_utils.LOGGER')
    @responses.activate
    def test_cielo24_error(self, mock_logger):
        """
        Test that when invalid cielo credentials are supplied, we get correct error response.
        """
        expected_error_message = 'Invalid credentials supplied.'
        responses.add(
            responses.GET,
            self.CIELO24_LOGIN_URL,
            body=json.dumps({'error': expected_error_message}),
            status=status.HTTP_400_BAD_REQUEST
        )

        credentials = {
            'org': 'test',
            'provider': TranscriptProviderType.CIELO24,
            'api_key': 'test-api-key',
            'username': 'test-cielo-user',
            'api_secret_key': ''
        }
        error_type, error_message, _ = validate_transcript_credentials(**credentials)
        self.assertEqual(error_type, TranscriptionProviderErrorType.INVALID_CREDENTIALS)
        self.assertEqual(error_message, expected_error_message)

        mock_logger.warning.assert_called_with(
            '[Transcript Credentials] Unable to get api token --  response %s --  status %s.',
            json.dumps({'error': error_message}),
            status.HTTP_400_BAD_REQUEST
        )

    @data(
        {
            'provider': 'unsupported-provider'
        },
        {
            'org': 'test',
            'api_key': 'test-api-key'
        }
    )
    def test_transcript_credentials_invalid_provider(self, credentials):
        """
        Test that validating credentials gives proper error in case of invalid provider.
        """
        provider = credentials.pop('provider', '')
        error_type, error_message, _ = validate_transcript_credentials(provider, **credentials)
        self.assertEqual(error_type, TranscriptionProviderErrorType.INVALID_PROVIDER)
        self.assertEqual(error_message, 'Invalid provider {provider}.'.format(provider=provider))

    @data(
        (
                {'provider': TranscriptProviderType.CIELO24},
                'org and api_key and username'
        ),
        (
                {'provider': TranscriptProviderType.THREE_PLAY_MEDIA},
                'org and api_key and api_secret_key'
        ),
        (
                {'provider': TranscriptProviderType.CIELO24, 'org': 'test-org'},
                'api_key and username'
        ),
        (
                {'provider': TranscriptProviderType.CIELO24, 'org': 'test-org', 'api_key': 'test-api-key'},
                'username'
        ),
        (
                {'org': 'test', 'provider': TranscriptProviderType.THREE_PLAY_MEDIA, 'api_key': 'test-api-key'},
                'api_secret_key'
        )
    )
    @unpack
    def test_transcript_credentials_error(self, credentials, missing_keys):
        """
        Test that validating credentials gives proper error in case of invalid input.
        """
        provider = credentials.pop('provider')
        expected_error_message = '{missing} must be specified for {provider}.'.format(
            provider=provider,
            missing=missing_keys
        )
        error_type, error_message, _ = validate_transcript_credentials(provider, **credentials)
        self.assertEqual(error_type, TranscriptionProviderErrorType.MISSING_REQUIRED_ATTRIBUTES)
        self.assertEqual(error_message, expected_error_message)
