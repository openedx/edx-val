# -*- coding: utf-8 -*-
"""
Tests for the API for Video Abstraction Layer
"""

import mock

from django.test import TestCase
from django.db import DatabaseError
from django.core.urlresolvers import reverse
from django.core.exceptions import ValidationError
from rest_framework import status
from rest_framework.test import APITestCase
from ddt import ddt, data

from edxval.models import Profile, Video, EncodedVideo
from edxval import api as api
from edxval.api import ValCannotCreateError
from edxval.serializers import VideoSerializer
from edxval.tests import constants

@ddt
class CreateVideoTest(TestCase):
    """
    Tests the create_video function in api.py.

    This function requires that a Profile object exist.
    """

    def setUp(self):
        """
        Creation of Profile objects that will be used to test video creation
        """
        api.create_profile(constants.PROFILE_DICT_DESKTOP)
        api.create_profile(constants.PROFILE_DICT_MOBILE)

    def test_create_video(self):
        """
        Tests the creation of a video
        """
        video_data = dict(
            encoded_videos=[
                constants.ENCODED_VIDEO_DICT_FISH_MOBILE
            ],
            **constants.VIDEO_DICT_FISH
        )
        result = api.create_video(video_data)
        videos = Video.objects.all()
        self.assertEqual(len(videos), 1)
        self.assertEqual("super-soaker", result)

    @data(
        constants.VIDEO_DICT_FISH,
        constants.VIDEO_DICT_NEGATIVE_DURATION,
        constants.VIDEO_DICT_INVALID_ID
    )
    def test_create_invalid_video(self, data): # pylint: disable=W0621
        """
        Tests the creation of a video with invalid data
        """
        with self.assertRaises(ValCannotCreateError):
            api.create_video(data)

    def test_invalid_profile(self):
        """
        Tests inputting bad profile type
        """
        video_data = dict(
            encoded_videos=[
                dict(
                    profile = constants.PROFILE_DICT_MOBILE,
                    **constants.ENCODED_VIDEO_DICT_MOBILE
                )
            ],
            **constants.VIDEO_DICT_FISH
        )
        with self.assertRaises(ValidationError):
            api.create_video(video_data)


@ddt
class CreateProfileTest(TestCase):
    """
    Tests the create_profile function in the api.py
    """

    def test_create_profile(self):
        """
        Tests the creation of a profile
        """
        result = api.create_profile(constants.PROFILE_DICT_DESKTOP)
        profiles = Profile.objects.all()
        self.assertEqual(len(profiles), 1)
        self.assertEqual(
            profiles[0].profile_name,
            constants.PROFILE_DICT_DESKTOP.get('profile_name')
        )
        self.assertEqual(len(profiles), 1)
        self.assertEqual("desktop", result)

    @data(
        constants.PROFILE_DICT_NEGATIVE_WIDTH,
        constants.PROFILE_DICT_NEGATIVE_HEIGHT,
        constants.PROFILE_DICT_MISSING_EXTENSION,
        constants.PROFILE_DICT_MANY_INVALID,
        constants.PROFILE_DICT_INVALID_NAME,
    )
    def test_invalid_create_profile(self, data): # pylint: disable=W0621
        """
        Tests the creation of invalid profile data
        """
        with self.assertRaises(ValCannotCreateError):
            api.create_profile(data)


class GetVideoInfoTest(TestCase):
    """
    Tests for our get_video_info function in api.py
    """

    def setUp(self):
        """
        Creates EncodedVideo objects in database
        """
        Profile.objects.create(**constants.PROFILE_DICT_MOBILE)
        Profile.objects.create(**constants.PROFILE_DICT_DESKTOP)
        Video.objects.create(**constants.VIDEO_DICT_FISH)
        EncodedVideo.objects.create(
            video=Video.objects.get(
                edx_video_id=constants.VIDEO_DICT_FISH.get("edx_video_id")
            ),
            profile=Profile.objects.get(profile_name="mobile"),
            **constants.ENCODED_VIDEO_DICT_MOBILE
        )
        EncodedVideo.objects.create(
            video=Video.objects.get(
                edx_video_id=constants.VIDEO_DICT_FISH.get("edx_video_id")
            ),
            profile=Profile.objects.get(profile_name="desktop"),
            **constants.ENCODED_VIDEO_DICT_DESKTOP
        )

    def test_get_video_found(self):
        """
        Tests for successful video request
        """
        self.assertIsNotNone(
            api.get_video_info(
                constants.VIDEO_DICT_FISH.get("edx_video_id")
            )
        )

    def test_no_such_video(self):
        """
        Tests searching for a video that does not exist
        """

        with self.assertRaises(api.ValVideoNotFoundError):
            api.get_video_info("non_existant-video__")
        with self.assertRaises(api.ValVideoNotFoundError):
            api.get_video_info("")

    def test_unicode_input(self):
        """
        Tests if unicode inputs are handled correctly
        """
        with self.assertRaises(api.ValVideoNotFoundError):
            api.get_video_info(u"๓ﻉѻฝ๓ٱซ")

    @mock.patch.object(VideoSerializer, '__init__')
    def test_force_internal_error(self, mock_init):
        """
        Tests to see if an unknown error will be handled
        """
        mock_init.side_effect = Exception("Mock error")
        with self.assertRaises(api.ValInternalError):
            api.get_video_info(
                constants.VIDEO_DICT_FISH.get("edx_video_id")
            )

    @mock.patch.object(Video.objects, 'get')
    def test_force_database_error(self, mock_get):
        """
        Tests to see if an database error will be handled
        """
        mock_get.side_effect = DatabaseError("DatabaseError")
        with self.assertRaises(api.ValInternalError):
            api.get_video_info(
                constants.VIDEO_DICT_FISH.get("edx_video_id")
            )


class GetVideoInfoTestWithHttpCalls(APITestCase):
    """
    Tests for the get_info_video, using the HTTP requests to populate database
    """

    def setUp(self):
        """
        Creates EncodedVideo objects in database with HTTP requests.

        The tests are similar to the GetVideoInfoTest class. This class
        is to tests that we have the same results, using a populated
        database via HTTP uploads.
        """
        Profile.objects.create(**constants.PROFILE_DICT_MOBILE)
        Profile.objects.create(**constants.PROFILE_DICT_DESKTOP)
        url = reverse('video-list')
        response = self.client.post(
            url, constants.COMPLETE_SET_FISH, format='json'
        )
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

    def test_get_video_found(self):
        """
        Tests for successful video request
        """
        self.assertIsNotNone(
            api.get_video_info(
                constants.COMPLETE_SET_FISH.get("edx_video_id")
            )
        )

    def test_get_info_queries_for_two_encoded_video(self):
        """
        Tests number of queries for a Video/EncodedVideo(1) pair
        """
        with self.assertNumQueries(5):
            api.get_video_info(constants.COMPLETE_SET_FISH.get("edx_video_id"))

    def test_get_info_queries_for_one_encoded_video(self):
        """
        Tests number of queries for a Video/EncodedVideo(1) pair
        """
        url = reverse('video-list')
        response = self.client.post(
            url, constants.COMPLETE_SET_STAR, format='json'
        )
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        with self.assertNumQueries(4):
            api.get_video_info(constants.COMPLETE_SET_STAR.get("edx_video_id"))

    def test_get_info_queries_for_only_video(self):
        """
        Tests number of queries for a Video with no Encoded Videopair
        """
        url = reverse('video-list')
        response = self.client.post(
            url, constants.VIDEO_DICT_ZEBRA, format='json'
        )
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        with self.assertNumQueries(3):
            api.get_video_info(constants.VIDEO_DICT_ZEBRA.get("edx_video_id"))

