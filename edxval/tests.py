"""
Tests for Video Abstraction Layer models
"""

from django.test import TestCase
from edxval.models import Video, Encoding, Profile


class ModelTest(TestCase):

    def setUp(self):
        Video.objects.create(
            edx_uid="edx123",
            title="CS101"
            )
        Profile.objects.create(
            title="ex",
            name="sample",
            extension="mp4",
            width=2880,
            height=1800,
            bitrate=64440,
            )

    def test_get_resolution(self):
        profile = Profile.objects.get(name="sample")
        self.assertEqual(profile.get_resolution(), "2880x1800")

    def test_time_update(self):
        pass

# Example i made for learning/reference
# def test_encoding_model_creation(self):
#     encoding = Encoding.objects.create(
#                             profile=Profile.objects.get(name="sample"),
#                             video=Video.objects.get(title="CS101"),
#                             file_size=4,
#                             duration=5)
#     self.assertEqual(str(encoding), \
#         "Encoding(video=Video(edx_uid=edx123, title=CS101), "\
#         "profile=Profile(title=ex, name=sample, extension=mp4, "\
#         "width=2880, height=1800, bitrate=64440), file_size=4, duration=5)")

