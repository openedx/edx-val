# -*- coding: utf-8 -*-
"""
Tests for transcript utils.
"""
import ddt
import json
import textwrap
import unittest

from edxval.transcript_utils import Transcript
from edxval.exceptions import TranscriptsGenerationException


@ddt.ddt
class TestTranscriptUtils(unittest.TestCase):
    """
    Tests transcripts conversion util.
    """
    def setUp(self):
        super(TestTranscriptUtils, self).setUp()

        self.srt_transcript = textwrap.dedent("""\
            0
            00:00:10,500 --> 00:00:13,000
            Elephant&#39;s Dream 大象的梦想

            1
            00:00:15,000 --> 00:00:18,000
            At the left we can see...

        """)

        self.sjson_transcript = textwrap.dedent("""\
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
        """)

    @ddt.data(
        ('invalid_input_format', 'sjson'),
        ('sjson', 'invalid_output_format'),
        ('invalid_input_format', 'invalid_output_format')
    )
    @ddt.unpack
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
        invalid_srt_transcript = 'invalid SubRip file content'
        with self.assertRaises(TranscriptsGenerationException):
            Transcript.convert(invalid_srt_transcript, 'srt', 'sjson')
