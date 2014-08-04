# -*- coding: utf-8 -*-
"""
Tests the serializers for the Video Abstraction Layer
"""

from django.test import TestCase

from edxval.serializers import (
    OnlyEncodedVideoSerializer,
    EncodedVideoSetSerializer,
    ProfileSerializer,
    VideoSerializer
)
from edxval.models import Profile
from edxval.tests import constants


class SerializerTests(TestCase):
    """
    Tests the Serializers
    """
    def setUp(self):
        """
        Creates EncodedVideo objects in database
        """
        Profile.objects.create(**constants.PROFILE_DICT_MOBILE)
        Profile.objects.create(**constants.PROFILE_DICT_NON_LATIN)

    def test_negative_fields_only_encoded_video(self):
        """
        Tests negative inputs for OnlyEncodedSerializer

        Tests negative inputs for bitrate, file_size in EncodedVideo
        """
        a = OnlyEncodedVideoSerializer(
            data=constants.ENCODED_VIDEO_DICT_NEGATIVE_BITRATE).errors
        self.assertEqual(a.get('bitrate')[0],
                         u"Ensure this value is greater than or equal to 0.")
        b = OnlyEncodedVideoSerializer(
            data=constants.ENCODED_VIDEO_DICT_NEGATIVE_FILESIZE).errors
        self.assertEqual(b.get('file_size')[0],
                         u"Ensure this value is greater than or equal to 0.")

    def test_negative_fields_video_set(self):
        """
        Tests negative inputs for EncodedVideoSetSerializer

        Tests negative inputs for duration in model Video
        """
        c = EncodedVideoSetSerializer(
            data=constants.VIDEO_DICT_NEGATIVE_DURATION).errors
        self.assertEqual(c.get('duration')[0],
                         u"Ensure this value is greater than or equal to 0.")

    def test_unicode_inputs(self):
        """
        Tests if the serializers can accept non-latin chars
        """
        self.assertIsNotNone(
            ProfileSerializer(Profile.objects.get(profile_name="배고파"))
        )

    def test_invalid_edx_video_id(self):
        """
        Test the Video model regex validation for edx_video_id field
        """
        error = VideoSerializer(data=constants.VIDEO_DICT_INVALID_ID).errors
        message = error.get("edx_video_id")[0]
        self.assertEqual(
            message,
            u"edx_video_id has invalid characters")