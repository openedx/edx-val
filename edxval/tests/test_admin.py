"""
Admin Module Test Cases
"""


from django.contrib.admin.sites import AdminSite
from django.contrib.messages.storage.fallback import FallbackStorage
from django.http import HttpRequest
from django.test import TestCase

from edxval.admin import ProfileAdmin
from edxval.models import Profile


class AdminTestCase(TestCase):
    """
    Test Case module for Profile Admin
    """
    def setUp(self):
        super(AdminTestCase, self).setUp()
        self.request = HttpRequest()
        self.conf_admin = ProfileAdmin(Profile, AdminSite())
        self.request.session = 'session'
        self.request._messages = FallbackStorage(self.request)  # pylint: disable=protected-access

    def test_default_fields(self):
        """
        Test: checking fields
        """
        self.assertEqual(
            list(self.conf_admin.get_form(self.request).base_fields),
            ['profile_name']
        )
