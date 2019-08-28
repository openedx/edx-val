# -*- coding: utf-8 -*-

from __future__ import absolute_import
from django.test import TestCase

from edxval.models import Video, VideoTranscript
from edxval.tests import constants


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

        self.assertFalse('\n' in video_trancript.filename)
