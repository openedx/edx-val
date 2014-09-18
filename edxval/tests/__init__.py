"""
init
"""
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
        self.client.logout()

    def _login(self, unauthorized=False):
        if unauthorized:
            username = password = 'unauthorized'
        else:
            username, password = self.username, self.password
        print self.client.login(username=username, password=password)
