"""
init
"""
from django.contrib.auth.models import User, Permission
from rest_framework.test import APITestCase


class APIAuthTestCase(APITestCase):
    """
    TestCase that creates a readwrite and readonly user in setUp
    """
    def setUp(self):
        self.username = self.password = 'readwrite'
        self.readwrite_user = User.objects.create_user(self.username, password=self.password)
        self.readwrite_user.user_permissions = Permission.objects.filter(content_type__app_label='edxval')
        self.readonly_user = User.objects.create_user('readonly', 'readonly')
        self._login()

    def _logout(self):
        self.client.logout()

    def _login(self, readonly=False):
        if readonly:
            username = password = 'readonly'
        else:
            username, password = self.username, self.password
        self.client.login(username=username, password=password)
