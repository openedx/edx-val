"""
init
"""
from __future__ import absolute_import
from django.contrib.auth.models import User, Permission
from rest_framework.test import APITestCase


class APIAuthTestCase(APITestCase):
    """
    TestCase that creates a readwrite and an unauthorized user in setUp
    """
    def setUp(self):
        self.username = self.password = 'readwrite'
        self.readwrite_user = User.objects.create_user(self.username, password=self.password)
        self.readwrite_user.user_permissions = Permission.objects.filter(content_type__app_label='edxval')
        self.readonly_user = User.objects.create_user('unauthorized', password='unauthorized')
        self._login()

    def _logout(self):
        """
        Logs out API user
        """
        self.client.logout()

    def _login(self, unauthorized=False):
        """
        Logs in user for test if authorized
        """
        if unauthorized:
            username = password = 'unauthorized'
        else:
            username, password = self.username, self.password
        self.client.login(username=username, password=password)
