# -*- coding: utf-8 -*-
"""
Tests the serializers for the Video Abstraction Layer
"""

from django.test import TestCase

from edxval.serializers import (
    EncodedVideoSerializer,
    ProfileSerializer,
    VideoSerializer,
)
from edxval.models import Profile, Video, EncodedVideo
from edxval.tests import constants


class SerializerTests(TestCase):
    """
    Tests the Serializers
    """
    def setUp(self):
        """
        Creates Profile objects
        """
        Profile.objects.create(**constants.PROFILE_DICT_MOBILE)
        Profile.objects.create(**constants.PROFILE_DICT_DESKTOP)
        Profile.objects.create(**constants.PROFILE_DICT_NON_LATIN)

    def test_negative_fields_for_encoded_video_serializer(self):
        """
        Tests negative inputs for EncodedVideoSerializer

        Tests negative inputs for bitrate, file_size in EncodedVideo
        """
        a = EncodedVideoSerializer(
            data=constants.ENCODED_VIDEO_DICT_NEGATIVE_BITRATE).errors
        self.assertEqual(a.get('bitrate')[0],
                         u"Ensure this value is greater than or equal to 0.")
        b = EncodedVideoSerializer(

            data=constants.ENCODED_VIDEO_DICT_NEGATIVE_FILESIZE).errors
        self.assertEqual(b.get('file_size')[0],
                         u"Ensure this value is greater than or equal to 0.")

    def test_negative_fields_for_video_serializer(self):
        """
        Tests negative inputs for VideoSerializer

        Tests negative inputs for duration in model Video
        """
        c = VideoSerializer(
            data=constants.VIDEO_DICT_NEGATIVE_DURATION).errors
        self.assertEqual(c.get('duration')[0],
                         u"Ensure this value is greater than or equal to 0.")

    def test_non_latin_serialization(self):
        """
        Tests if the serializers can accept non-latin chars
        """
        #TODO not the best test. Need to understand what result we want
        self.assertIsInstance(
            ProfileSerializer(Profile.objects.get(profile_name="배고파")),
            ProfileSerializer
        )

    def test_non_latin_deserialization(self):
        """
        Tests deserialization of non-latin data
        """
        #TODO write a test for this when we understand what we want
        pass

    def test_invalid_edx_video_id(self):
        """
        Test the Video model regex validation for edx_video_id field
        """
        error = VideoSerializer(data=constants.VIDEO_DICT_INVALID_ID).errors
        message = error.get("edx_video_id")[0]
        self.assertEqual(
            message,
            u"edx_video_id has invalid characters")

    def test_encoded_video_set_output(self):
        """
        Tests for basic structure of EncodedVideoSetSerializer
        """
        video = Video.objects.create(**constants.VIDEO_DICT_COAT)
        EncodedVideo.objects.create(
            video=video,
            profile=Profile.objects.get(profile_name="desktop"),
            **constants.ENCODED_VIDEO_DICT_DESKTOP
        )
        EncodedVideo.objects.create(
            video=video,
            profile=Profile.objects.get(profile_name="mobile"),
            **constants.ENCODED_VIDEO_DICT_MOBILE
        )
        result = VideoSerializer(video).data
        # Check for 2 EncodedVideo entries
        self.assertEqual(len(result.get("encoded_videos")), 2)
        # Check for original Video data
        self.assertDictContainsSubset(constants.VIDEO_DICT_COAT, result)
