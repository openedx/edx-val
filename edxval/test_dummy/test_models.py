"""
Tests for Video Abstraction Layer models
"""

from django.test import TestCase
from edxval.models import Video, Encoding, Profile


class ModelTest(TestCase):

    def setUp(self):
        print "does this work"
        Profile.objects.create(name="sample", width=2880, height=1800)

    def test_get_resolution(self):
        profile = Profile.objects.get(name="sample")
        self.assertEqual(profile.get_resolution(), "2880x1800")
        print "does this run"
