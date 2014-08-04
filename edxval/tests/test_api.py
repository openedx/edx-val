# -*- coding: utf-8 -*-
"""
Tests for the API for Video Abstraction Layer
"""

import mock

from django.test import TestCase
from django.db import DatabaseError

from edxval.models import Profile, Video, EncodedVideo
from edxval import api as api
from edxval.serializers import EncodedVideoSetSerializer
from edxval.tests import constants


class GetVideoInfoTest(TestCase):

#TODO When upload portion is finished, do not forget to create tests for validating
#TODO regex for models. Currently, objects are created manually and validators
#TODO are not triggered.
    def setUp(self):
        """
        Creates EncodedVideo objects in database
        """
        Profile.objects.create(**constants.PROFILE_DICT_MOBILE)
        Profile.objects.create(**constants.PROFILE_DICT_DESKTOP)
        Video.objects.create(**constants.VIDEO_DICT_COAT)
        EncodedVideo.objects.create(
            video=Video.objects.get(
                edx_video_id=constants.VIDEO_DICT_COAT.get("edx_video_id")
            ),
            profile=Profile.objects.get(profile_name="mobile"),
            **constants.ENCODED_VIDEO_DICT_MOBILE
        )
        EncodedVideo.objects.create(
            video=Video.objects.get(
                edx_video_id=constants.VIDEO_DICT_COAT.get("edx_video_id")
            ),
            profile=Profile.objects.get(profile_name="desktop"),
            **constants.ENCODED_VIDEO_DICT_DESKTOP
        )

    def test_get_video_found(self):
        """
        Tests for successful video request
        """
        self.assertIsNotNone(api.get_video_info(constants.EDX_VIDEO_ID))

    def test_no_such_video(self):
        """
        Tests searching for a video that does not exist
        """
        with self.assertRaises(api.ValVideoNotFoundError):
            api.get_video_info("non_existing-video__")

    def test_unicode_input(self):
        """
        Tests if unicode inputs are handled correctly
        """
        with self.assertRaises(api.ValVideoNotFoundError):
            api.get_video_info(u"๓ﻉѻฝ๓ٱซ")

    @mock.patch.object(EncodedVideoSetSerializer, '__init__')
    def test_force_internal_error(self, mock_init):
        """
        Tests to see if an unknown error will be handled
        """
        mock_init.side_effect = Exception("Mock error")
        with self.assertRaises(api.ValInternalError):
            api.get_video_info(constants.EDX_VIDEO_ID)

    @mock.patch.object(Video.objects, 'get')
    def test_force_database_error(self, mock_get):
        """
        Tests to see if an database error will be handled
        """
        mock_get.side_effect = DatabaseError("DatabaseError")
        with self.assertRaises(api.ValInternalError):
            api.get_video_info(constants.EDX_VIDEO_ID)
