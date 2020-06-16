# -*- coding: utf-8 -*-
"""
Tests the serializers for the Video Abstraction Layer
"""
from django.test import TestCase

from edxval.models import EncodedVideo, Profile, Video
from edxval.serializers import EncodedVideoSerializer, VideoSerializer
from edxval.tests import constants


class SerializerTests(TestCase):
    """
    Tests the Serializers
    """

    def setUp(self):
        """
        Creates Profile objects and a video object
        """
        super(SerializerTests, self).setUp()
        Profile.objects.create(profile_name=constants.PROFILE_MOBILE)
        Profile.objects.create(profile_name=constants.PROFILE_DESKTOP)
        Video.objects.create(
            duration=0,
            edx_video_id=constants.VIDEO_DICT_NON_LATIN_ID["edx_video_id"],
            status='test'
        )

    def test_negative_fields_for_encoded_video_serializer(self):
        """
        Tests negative inputs for EncodedVideoSerializer

        Tests negative inputs for bitrate, file_size in EncodedVideo
        """
        serializer = EncodedVideoSerializer(data=constants.ENCODED_VIDEO_DICT_NEGATIVE_BITRATE)
        self.assertFalse(serializer.is_valid())
        self.assertEqual(
            serializer.errors.get('bitrate')[0],
            u"Ensure this value is greater than or equal to 0."
        )

        serializer = EncodedVideoSerializer(data=constants.ENCODED_VIDEO_DICT_NEGATIVE_FILESIZE)
        self.assertFalse(serializer.is_valid())
        self.assertEqual(
            serializer.errors.get('file_size')[0],
            u"Ensure this value is greater than or equal to 0."
        )

    def test_negative_fields_for_video_serializer(self):
        """
        Tests negative inputs for VideoSerializer

        Tests negative inputs for duration in model Video
        """
        serializer = VideoSerializer(data=constants.VIDEO_DICT_NEGATIVE_DURATION)
        self.assertFalse(serializer.is_valid())
        self.assertEqual(
            serializer.errors.get('duration')[0],
            u"Ensure this value is greater than or equal to 0."
        )

    def test_non_latin_serialization(self):
        """
        Tests if the serializers can accept non-latin chars
        """
        # TODO not the best test. Need to understand what result we want
        self.assertIsInstance(
            VideoSerializer(
                Video.objects.get(edx_video_id=constants.VIDEO_DICT_NON_LATIN_ID["edx_video_id"])
            ),
            VideoSerializer
        )

    def test_invalid_edx_video_id(self):
        """
        Test the Video model regex validation for edx_video_id field
        """
        serializer = VideoSerializer(data=constants.VIDEO_DICT_INVALID_ID)
        self.assertFalse(serializer.is_valid())
        message = serializer.errors.get("edx_video_id")[0]
        self.assertEqual(
            message,
            u"edx_video_id has invalid characters"
        )

    def test_invalid_course_id(self):
        serializer = VideoSerializer(
            data={
                "edx_video_id": "dummy",
                "client_video_id": "dummy",
                "duration": 0,
                "status": "dummy",
                "encoded_videos": [],
                "courses": ["x" * 300],
            }
        )
        self.assertFalse(serializer.is_valid())
        self.assertEqual(
            str(serializer.errors.get('courses').get('course_id')[0]),
            "Ensure this value has at most 255 characters (it has 300)."
        )

    def test_encoded_video_set_output(self):
        """
        Tests for basic structure of EncodedVideoSetSerializer
        """
        video = Video.objects.create(**constants.VIDEO_DICT_FISH)
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
        EncodedVideo.objects.create(
            video=video,
            profile=Profile.objects.get(profile_name="hls"),
            **constants.ENCODED_VIDEO_DICT_HLS
        )
        result = VideoSerializer(video).data
        # Check for 3 EncodedVideo entries
        self.assertEqual(len(result.get("encoded_videos")), 3)
        # Check for original Video data
        matching_dict = {k: v for k, v in result.items() if k in constants.VIDEO_DICT_FISH}
        assert constants.VIDEO_DICT_FISH == matching_dict

    def test_no_profile_validation(self):
        """
        Tests when there are no profiles to validation when deserializing
        """

        data = dict(
            encoded_videos=[
                constants.ENCODED_VIDEO_DICT_MOBILE
            ],
            **constants.VIDEO_DICT_FISH
        )
        serializer = VideoSerializer(data=data)
        self.assertFalse(serializer.is_valid())
        self.assertEqual(
            serializer.errors.get("encoded_videos"),
            [{"profile": ["This field is required."]}]
        )

    def test_wrong_input_type(self):
        """
        Tests an non dict input in the VideoSerializer
        """
        data = "hello"
        serializer = VideoSerializer(data=data)
        self.assertFalse(serializer.is_valid())
        self.assertEqual(
            serializer.errors.get("non_field_errors")[0],
            "Invalid data. Expected a dictionary, but got str."
        )
