from django.core.urlresolvers import reverse
from rest_framework import status
from rest_framework.test import APITestCase

from edxval.tests import constants


class VideoListTest(APITestCase):
    """
    Tests the creations of Videos via POST/GET
    """

    def test_post_video(self):
        """
        Tests creating a new Video object via POST
        """
        url = reverse('video_view')
        response = self.client.post(
            url, [constants.VIDEO_DICT_LION], format='json'
        )
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

    def test_get_all_videos(self):
        """
        Tests getting all Video objects
        """
        url = reverse('video_view')
        self.client.post(url, [constants.VIDEO_DICT_LION], format='json')
        self.client.post(url, [constants.VIDEO_DICT_CATS], format='json')
        videos = len(self.client.get("/edxval/video/").data)
        self.assertEqual(videos, 2)

    def test_post_multiple_valid_video_creation(self):
        """
        Tests the creation of more than one video
        """
        url = reverse('video_view')
        response = self.client.post(
            url, constants.VIDEO_DICT_TIGERS_BEARS, format='json'
        )
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        videos = len(self.client.get("/edxval/video/").data)
        self.assertEqual(videos, 2)

    def test_post_invalid_video_entry(self):
        """
        Tests for invalid video entry for POST
        """
        url = reverse('video_view')
        response = self.client.post(url, [constants.VIDEO_DICT_INVALID_ID], format='json')
        error = len(response.data)
        self.assertEqual(error, 1)

    def test_post_invalid_entry(self):
        """
        Tests when a non list POST request is made
        """
        url = reverse('video_view')
        response = self.client.post(url, constants.VIDEO_DICT_CATS, format='json')
        self.assertEqual(response.data, "Not a list: <type 'dict'>")

    def test_post_invalid_video_dict_list(self):
        """
        Tests when there are valid and invalid dicts in list
        """
        url = reverse('video_view')
        response = self.client.post(url, constants.VIDEO_DICT_INVALID_SET, format='json')
        errors = len(response.data)
        self.assertEqual(errors, 2)
        videos = len(self.client.get("/edxval/video/").data)
        self.assertEqual(videos, 1)

    def test_post_valid_video_dict_list_duplicates(self):
        """
        Tests when valid duplicate dicts are submitted in a list
        """
        url = reverse('video_view')
        response = self.client.post(url, constants.VIDEO_DICT_DUPLICATES, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        videos = len(self.client.get("/edxval/video/").data)
        self.assertEqual(videos, 1)

    def test_post_non_latin_dict(self):
        """
        Tests a non-latin character input
        """
        url = reverse('video_view')
        response = self.client.post(url, [constants.VIDEO_DICT_NON_LATIN_ID], format='json')
        errors = len(response.data)
        self.assertEqual(errors, 1)
        response = self.client.post(url, [constants.VIDEO_DICT_NON_LATIN_TITLE], format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

    def test_post_update_video(self):
        """
        Tests video update
        """
        url = reverse('video_view')
        self.client.post(url, [constants.VIDEO_DICT_LION], format='json')
        response = self.client.post(url, [constants.VIDEO_DICT_LION2], format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        videos = len(self.client.get("/edxval/video/").data)
        self.assertEqual(videos, 1)
        old_duration = constants.VIDEO_DICT_LION.get("duration")
        new_duration = constants.VIDEO_DICT_LION2.get("duration")
        self.assertNotEqual(new_duration, old_duration)


class VideoDetailTest(APITestCase):
    """
    Tests for the VideoDetail class
    """

    def test_get_video(self):
        """
        Tests retrieving a particular Video Object
        """
        url = reverse('video_view')
        self.client.post(url, [constants.VIDEO_DICT_LION], format='json')
        search = "/edxval/video/{0}".format(constants.VIDEO_DICT_LION.get("edx_video_id"))
        response = self.client.get(search)
        a = response.data.get("edx_video_id")
        b = constants.VIDEO_DICT_LION.get("edx_video_id")
        self.assertEqual(a, b)
