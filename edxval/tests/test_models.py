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
            bitrate=64440,
        )
        Video.objects.create(
            title="sample",
            duration=1000,
            edx_video_id='example',
        )
        EncodedVideo.objects.create(
            title="ev",
            url="meow.com",
            file_size=123345,
            video=Video.objects.get(title="sample"),
            profile=Profile.objects.get(profile_name="sample"),
        )

    def test_time_modified(self):
        ev = EncodedVideo.objects.get(title="ev")
        ev.url = "woof.com"
        self.assertNotEqual(ev.created, ev.modified)