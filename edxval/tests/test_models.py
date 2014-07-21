"""
Tests for Video Abstraction Layer models
"""

from django.test import TestCase
from edxval.models import Video, EncodedVideo, Profile


class ModelTest(TestCase):

    def setUp(self):

        Profile.objects.create(
            profile_id="ex",
            profile_name="sample",
            extension="mp4",
            width=2880,
            height=1800,
        )
        Video.objects.create(
            client_title="sample",
            duration=1000,
            video_prefix='example',
        )
        EncodedVideo.objects.create(
            edx_video_id="ev",
            url="meow.com",
            file_size=123345,
            video=Video.objects.get(client_title="sample"),
            profile=Profile.objects.get(profile_name="sample"),
            bitrate=64440,
        )

    def test_time_modified(self):
        """
        Tests to see if the time updated when the object is updated
        """
        ev = EncodedVideo.objects.get(edx_video_id="ev")
        ev.url = "woof.com"
        self.assertNotEqual(ev.created, ev.modified)