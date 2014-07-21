# -*- coding: utf-8 -*-
"""
Tests the serializers for the Video Abstraction Layer
"""

from django.test import TestCase

from edxval.serializers import (
    OnlyEncodedVideoSerializer,
    EncodedVideoSetSerializer,
    ProfileSerializer
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

    def test_negative_fields(self):
        """
        Tests negative inputs for a serializer

        Tests negative inputs for bitrate, file_size in EncodedVideo,
        and duration in Video
        """
        a = OnlyEncodedVideoSerializer(
            data=constants.ENCODED_VIDEO_DICT_NEGATIVE_BITRATE).errors
        self.assertEqual(a.get('bitrate')[0],
                         u"Ensure this value is greater than or equal to 1.")
        b = OnlyEncodedVideoSerializer(
            data=constants.ENCODED_VIDEO_DICT_NEGATIVE_FILESIZE).errors
        self.assertEqual(b.get('file_size')[0],
                         u"Ensure this value is greater than or equal to 1.")
        c = EncodedVideoSetSerializer(
            data=constants.VIDEO_DICT_NEGATIVE_DURATION).errors
        self.assertEqual(c.get('duration')[0],
                         u"Ensure this value is greater than or equal to 1.")

    def test_unicode_inputs(self):
        """
        Tests if the serializers can accept non-latin chars
        """
        self.assertIsNotNone(
            ProfileSerializer(Profile.objects.get(profile_name="배고파"))
        )