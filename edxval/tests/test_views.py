from django.core.urlresolvers import reverse
from rest_framework import status
from rest_framework.test import APITestCase

from edxval.tests import constants
from edxval.models import Profile


class VideoListTest(APITestCase):
    """
    Tests the creations of Videos via POST/GET
    """
    def setUp(self):
        """
        Used for manually creating profile objects which EncodedVideos require.
        """
        Profile.objects.create(**constants.PROFILE_DICT_MOBILE)
        Profile.objects.create(**constants.PROFILE_DICT_DESKTOP)

    """
    Tests for successful POST requests.

    These tests should be returning HTTP_201_CREATED responses.
    """
    def test_complete_set_two_encoded_video_post(self):
        """
        Tests POSTing Video and EncodedVideo pair
        """
        url = reverse('video-list')
        response = self.client.post(
            url, constants.COMPLETE_SET_FISH, format='json'
        )
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        video = self.client.get("/edxval/video/").data
        self.assertEqual(len(video), 1)
        self.assertEqual(len(video[0].get("encoded_videos")), 2)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

    def test_complete_set_with_extra_video_field(self):
        """
        Tests the case where there is an additional unneeded video field vis POST
        """
        url = reverse('video-list')
        response = self.client.post(
            url, constants.COMPLETE_SET_EXTRA_VIDEO_FIELD, format='json'
        )
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        video = self.client.get("/edxval/video/").data
        self.assertEqual(len(video), 1)
        edx_video_id = constants.VIDEO_DICT_STAR.get("edx_video_id")
        self.assertEqual(video[0].get("edx_video_id"), edx_video_id)

    def test_post_video(self):
        """
        Tests POSTing a new Video object and empty EncodedVideo
        """
        url = reverse('video-list')
        response = self.client.post(
            url, constants.VIDEO_DICT_ANIMAL, format='json'
        )
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        video = self.client.get("/edxval/video/").data
        self.assertEqual(len(video), 1)
        self.assertEqual(len(video[0].get("encoded_videos")), 0)

    def test_post_non_latin_client_video_id(self):
        """
        Tests POSTing non-latin client_video_id
        """
        url = reverse('video-list')
        response = self.client.post(url, constants.VIDEO_DICT_NON_LATIN_TITLE, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

    """
    Tests for POSTing invalid data

    These tests should be returning HTTP_400_BAD_REQUEST
    """
    def test_post_videos(self):
        """
        Tests POSTing same video.
        """
        url = reverse('video-list')
        response = self.client.post(
            url, constants.VIDEO_DICT_ANIMAL, format='json'
        )
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        videos = len(self.client.get("/edxval/video/").data)
        self.assertEqual(videos, 1)
        response = self.client.post(
            url, constants.VIDEO_DICT_ANIMAL, format='json'
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(
            response.data.get("edx_video_id")[0],
            "Video with this Edx video id already exists."
        )
        videos = len(self.client.get("/edxval/video/").data)
        self.assertEqual(videos, 1)

    def test_complete_set_invalid_encoded_video_post(self):
        """
        Tests POSTing valid Video and partial valid EncodedVideos.
        """
        url = reverse('video-list')
        response = self.client.post(
            url, constants.COMPLETE_SET_INVALID_ENCODED_VIDEO_FISH, format='json'
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        video = self.client.get("/edxval/video/").data
        self.assertEqual(len(video), 0)

    def test_complete_set_invalid_video_post(self):
        """
        Tests invalid Video POST
        """
        url = reverse('video-list')
        response = self.client.post(
            url, constants.COMPLETE_SET_INVALID_VIDEO_FISH, format='json'
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        video = self.client.get("/edxval/video/").data
        self.assertEqual(len(video), 0)
        self.assertEqual(
            response.data.get("edx_video_id")[0],
            "edx_video_id has invalid characters"
        )

    def test_post_invalid_video_entry(self):
        """
        Tests for invalid video entry for POST
        """
        url = reverse('video-list')
        response = self.client.post(url, constants.VIDEO_DICT_INVALID_ID, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        errors = response.data
        self.assertEqual(
            errors.get("edx_video_id")[0],
            "edx_video_id has invalid characters"
        )

    def test_post_non_latin_edx_video_id(self):
        """
        Tests POSTing non-latin edx_video_id
        """
        url = reverse('video-list')
        response = self.client.post(url, constants.VIDEO_DICT_NON_LATIN_ID, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        errors = response.data
        self.assertEqual(
            errors.get("edx_video_id")[0],
            "edx_video_id has invalid characters"
        )
    """
    Tests for number of queries
    """
    def test_queries_for_only_video(self):
        """
        Tests number of queries for a Video with no Encoded Videos
        """
        url = reverse('video-list')
        with self.assertNumQueries(3):
            self.client.post(url, constants.VIDEO_DICT_ZEBRA, format='json')

    def test_queries_for_two_encoded_video(self):
        """
        Tests number of queries for a Video/EncodedVideo(2) pair
        """
        url = reverse('video-list')
        with self.assertNumQueries(11):
            self.client.post(url, constants.COMPLETE_SET_FISH, format='json')

    def test_queries_for_single_encoded_videos(self):
        """
        Tests number of queries for a Video/EncodedVideo(1) pair
                """
        url = reverse('video-list')
        with self.assertNumQueries(7):
            self.client.post(url, constants.COMPLETE_SET_STAR, format='json')
    """
    Tests for GET
    """
    def test_get_all_videos(self):
        """
        Tests getting all Video objects
        """
        url = reverse('video-list')
        response = self.client.post(url, constants.VIDEO_DICT_ANIMAL, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        response = self.client.post(url, constants.VIDEO_DICT_ZEBRA, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        videos = self.client.get("/edxval/video/").data
        self.assertEqual(len(videos), 2)

    def test_queries_for_get(self):
        '''
        Tests number of queries when GETting all videos
        '''
        url = reverse('video-list')
        response = self.client.post(url, constants.VIDEO_DICT_ANIMAL, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        response = self.client.post(url, constants.VIDEO_DICT_ZEBRA, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        with self.assertNumQueries(2):
            self.client.get("/edxval/video/").data
        response = self.client.post(url, constants.COMPLETE_SET_FISH, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        with self.assertNumQueries(4):
            self.client.get("/edxval/video/").data
        response = self.client.post(url, constants.COMPLETE_SET_STAR, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        with self.assertNumQueries(5):
            self.client.get("/edxval/video/").data

