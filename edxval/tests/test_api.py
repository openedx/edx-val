"""
Tests for the API for Video Abstraction Layer
"""

from django.core.management import call_command
from django.test import TestCase

from edxval.models import Profile, Video, EncodedVideo
from edxval import api as api

VIDEO_QUERY = dict(
    video_name="cs101",
    video_format="mhq3gp",
)

VIDEO_QUERY_NO_VIDEO = dict(
    video_name="cats101",
    video_format="blqmp4",
)

VIDEO_QUERY_NO_FORMAT = dict(
    video_name="cs101",
    video_format="blqmp4",
)

ANSWER_URL = dict(
    url="meow.cs101.com/meow",
)


class ApiTest(TestCase):

    def setUp(self):
        call_command('loaddata',
                     'edxval/tests/fixtures/testing_data.json',
                     verbosity=0)

    def test_get_video_found(self):
        """
        Tests for successful video request
        """
        url = api.get_video_url(**VIDEO_QUERY)
        self.assertEqual(url, ANSWER_URL)

    def test_get_video_not_found(self):
        """
        Tests for no video found
        """
        with self.assertRaises(api.ValVideoNotFoundError):
            api.get_video_url(**VIDEO_QUERY_NO_VIDEO)

    def test_get_video_no_format(self):
        """
        Tests when video is found, but requested format is not found
        """
        with self.assertRaises(api.ValNotAvailableError):
            api.get_video_url(**VIDEO_QUERY_NO_FORMAT)

    def test_get_duration(self):
        """
        Tests addition of video durations for given course/section/subsection
        """
        pass
