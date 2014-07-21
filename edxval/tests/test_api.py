"""
Tests for the API for Video Abstraction Layer
"""

from django.test import TestCase

from edxval.models import Profile, Video, EncodedVideo
from edxval import api as api

from edxval.tests.constants import *


class ApiTest(TestCase):

    def setUp(self):
        Profile.objects.create(**P_DICT)
        Profile.objects.create(**P_DICT2)

    def test_create_upload(self):
        """
        Tests to see if existing video is updated
        """
        result = api.update_create_encoded_video(V_DICT, EV_DICT_CREATE, "mobile")
        self.assertEqual(result[0], "created")
        #TODO Write more assertions for object content

    def test_update_upload(self):
        """
        Tests to see if encoded video is created
        """
        api.update_create_encoded_video(V_DICT, EV_DICT_CREATE, "mobile")
        result = api.update_create_encoded_video(V_DICT, EV_DICT_UPDATE, "mobile")
        self.assertEqual(result[0], "updated")
        #TODO Write more assertions for object content
        #TODO Write more assertions for modified date

    # def test_get_video_found(self):
    #     """
    #     Tests for successful video request
    #     """
    #     pass
    #
    # def test_get_video_not_found(self):
    #     """
    #     Tests for no video found
    #     """
    #     pass
    #
    # def test_get_video_no_format(self):
    #     """
    #     Tests when video is found, but requested format is not found
    #     """
    #     pass
    #
    # def test_get_video_bad_format(self):
    #     """
    #     Tests for unknown video format
    #     """
    #     pass
    #
    # def test_get_duration(self):
    #     """
    #     Tests addition of video durations for given course/section/subsection
    #     """
    #     pass

    def test_if_valid_video_id(self):
        for i, j in edx_id_list:
            self.assertEqual(api._check_edx_video_id(i),j)