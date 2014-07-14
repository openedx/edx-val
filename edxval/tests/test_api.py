"""
Tests for the API for Video Abstraction Layer
"""

from django.core.management import call_command
from django.test import TestCase

from edxval.models import Profile, Video, EncodedVideo
from edxval import api as api

from edxval.tests.constants import *


class ApiTest(TestCase):

    def setUp(self):
        Profile.objects.create(**P_DICT)
        Profile.objects.create(**P_DICT2)

        #Video.objects.create(**vd)
        # call_command('loaddata',
        #              'edxval/tests/fixtures/testing_data.json',
        #              verbosity=0)

    def test_upload_creation(self):
        print api.deserialize_video_upload(V_DICT, JUST_EV_DICT ,"mobile")
        self.assertEqual(1, 2)

    # def test_create_encoded_video(self):
    #     """
    #     Tests to see if encoded video is created
    #     """
    #     self.assertEqual(api.update_or_create_encoded_video(EV_DICT), True)

    # def test_get_video_found(self):
    #     """
    #     Tests for successful video request
    #     """
    #     api.update_or_create_encoded_video(EV_DICT)
    #     api.update_or_create_encoded_video(EV_DICT2)
    #     url = api.get_video_info(**VIDEO_QUERY)
    #     self.assertEqual(url, "lol")
    #
    # def test_get_video_not_found(self):
    #     """
    #     Tests for no video found
    #     """
    #     with self.assertRaises(api.ValVideoNotFoundError):
    #         api.get_video_info(**VIDEO_QUERY_NO_VIDEO)
    #
    # # def test_get_video_no_format(self):
    # #     """
    # #     Tests when video is found, but requested format is not found
    # #     """
    # #     with self.assertRaises(api.ValNotAvailableError):
    # #         api.get_video_info(**VIDEO_QUERY_NO_FORMAT)
    #
    # def test_get_video_bad_format(self):
    #     """
    #     Tests for unknown video format
    #     """
    #     with self.assertRaises(api.ValRequestError):
    #         api.get_video_info(**BAD_VIDEO_FORMAT)
    #
    # def test_get_duration(self):
    #     """
    #     Tests addition of video durations for given course/section/subsection
    #     """
    #     with self.assertRaises(NotImplementedError):
    #         api.get_duration(course_id="123")
    #
    # def test_if_valid_video_id(self):
    #     for i, j in edx_id_list:
    #         self.assertEqual(api._check_edx_video_id(i),j)