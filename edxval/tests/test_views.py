 # pylint: disable=E1103, W0106
"""
Tests for Video Abstraction Layer views
"""
from django.core.urlresolvers import reverse
from rest_framework import status
from rest_framework.test import APITestCase

from edxval.tests import constants
from edxval.models import Profile, Video


class VideoDetail(APITestCase):
    """
    Tests Retrieve, Update and Destroy requests
    """

    def setUp(self):
        """
        Used for manually creating profile objects which EncodedVideos require.
        """
        Profile.objects.create(**constants.PROFILE_DICT_MOBILE)
        Profile.objects.create(**constants.PROFILE_DICT_DESKTOP)

    #Tests for successful PUT requests.

    def test_update_video(self):
        """
        Tests PUTting a single video with no encoded videos.
        """
        url = reverse('video-list')
        response = self.client.post(url, constants.VIDEO_DICT_ANIMAL, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        url = reverse(
            'video-detail',
            kwargs={"edx_video_id": constants.VIDEO_DICT_ANIMAL.get("edx_video_id")}
        )
        response = self.client.put(
            url,
            constants.VIDEO_DICT_UPDATE_ANIMAL,
            format='json'
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        videos = Video.objects.all()
        self.assertEqual(len(videos), 1)
        self.assertNotEqual(
            videos[0].duration,
            constants.VIDEO_DICT_ANIMAL.get("duration"))
        self.assertEqual(
            videos[0].duration,
            constants.VIDEO_DICT_UPDATE_ANIMAL.get("duration")
        )

    def test_update_one_encoded_video(self):
        """
        Tests PUTting one encoded video.
        """
        url = reverse('video-list')
        response = self.client.post(url, constants.COMPLETE_SET_STAR, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        url = reverse(
            'video-detail',
            kwargs={"edx_video_id": constants.COMPLETE_SET_STAR.get("edx_video_id")}
        )
        response = self.client.put(
            url,
            constants.COMPLETE_SET_UPDATE_STAR,
            format='json'
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        videos = Video.objects.all()
        self.assertEqual(len(videos), 1)
        self.assertEqual(len(videos[0].encoded_videos.all()), 1)
        new_url = videos[0].encoded_videos.all()[0].url
        self.assertNotEqual(
            constants.ENCODED_VIDEO_UPDATE_DICT_STAR,
            constants.ENCODED_VIDEO_DICT_STAR.get("url"))
        self.assertEqual(
            new_url,
            constants.ENCODED_VIDEO_UPDATE_DICT_STAR.get("url")
        )

    def test_update_two_encoded_videos(self):
        """
        Tests PUTting two encoded videos and then PUT back.
        """
        url = reverse('video-list')
        response = self.client.post(url, constants.COMPLETE_SET_FISH, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        url = reverse(
            'video-detail',
            kwargs={"edx_video_id": constants.COMPLETE_SET_FISH.get("edx_video_id")}
        )
        response = self.client.patch( # pylint: disable=E1101
            path=url,
            data=constants.COMPLETE_SET_UPDATE_FISH,
            format='json'
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        videos = Video.objects.all()
        self.assertEqual(len(videos), 1)
        self.assertEqual(len(videos[0].encoded_videos.all()), 2)
        first_url = videos[0].encoded_videos.all()[0].url
        self.assertNotEqual(
            constants.ENCODED_VIDEO_DICT_FISH_MOBILE,
            constants.ENCODED_VIDEO_DICT_UPDATE_FISH_MOBILE.get("url"))
        self.assertEqual(
            first_url,
            constants.ENCODED_VIDEO_DICT_UPDATE_FISH_MOBILE.get("url")
        )
        second_url = videos[0].encoded_videos.all()[1].url
        self.assertNotEqual(
            constants.ENCODED_VIDEO_DICT_FISH_DESKTOP,
            constants.ENCODED_VIDEO_DICT_UPDATE_FISH_DESKTOP.get("url"))
        self.assertEqual(
            second_url,
            constants.ENCODED_VIDEO_DICT_UPDATE_FISH_DESKTOP.get("url")
        )
        response = self.client.put(
            path=url,
            data=constants.COMPLETE_SET_FISH,
            format='json'
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        videos = Video.objects.all()
        self.assertEqual(len(videos), 1)
        first_url = videos[0].encoded_videos.all()[0].url
        self.assertEqual(
            first_url,
            constants.ENCODED_VIDEO_DICT_FISH_MOBILE.get("url")
        )
        second_url = videos[0].encoded_videos.all()[1].url
        self.assertEqual(
            second_url,
            constants.ENCODED_VIDEO_DICT_FISH_DESKTOP.get("url")
        )

    def test_update_one_of_two_encoded_videos(self):
        """
        Tests PUTting one of two EncodedVideo(s) and then a single EncodedVideo PUT back.
        """
        url = reverse('video-list')
        response = self.client.post(url, constants.COMPLETE_SET_FISH, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        url = reverse(
            'video-detail',
            kwargs={"edx_video_id": constants.COMPLETE_SET_FISH.get("edx_video_id")}
        )
        response = self.client.put(
            path=url,
            data=constants.COMPLETE_SET_FIRST_HALF_UPDATE_FISH,
            format='json'
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        videos = Video.objects.all()
        self.assertEqual(len(videos), 1)
        self.assertEqual(len(videos[0].encoded_videos.all()), 2)
        first_url = videos[0].encoded_videos.all()[0].url
        self.assertNotEqual(
            constants.ENCODED_VIDEO_DICT_FISH_MOBILE,
            constants.ENCODED_VIDEO_DICT_UPDATE_FISH_MOBILE.get("url"))
        self.assertEqual(
            first_url,
            constants.ENCODED_VIDEO_DICT_UPDATE_FISH_MOBILE.get("url")
        )
        second_url = videos[0].encoded_videos.all()[1].url
        self.assertEqual(
            second_url,
            constants.ENCODED_VIDEO_DICT_FISH_DESKTOP.get("url")
        )
        response = self.client.put(
            path=url,
            data=constants.COMPLETE_SET_UPDATE_ONLY_DESKTOP_FISH,
            format='json'
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        videos = Video.objects.all()
        self.assertEqual(len(videos), 1)
        first_url = videos[0].encoded_videos.all()[0].url
        self.assertEqual(
            first_url,
            constants.ENCODED_VIDEO_DICT_UPDATE_FISH_DESKTOP.get("url")
        )
        self.assertEqual(len(videos[0].encoded_videos.all()), 1)

    def test_update_invalid_video(self):
        """
        Tests PUTting a video with different edx_video_id.

        The new edx_video_id is ignored in the VideoDetail view.
        """
        url = reverse('video-list')
        response = self.client.post(url, constants.COMPLETE_SET_FISH, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        url = reverse(
            'video-detail',
            kwargs={"edx_video_id": constants.COMPLETE_SET_FISH.get("edx_video_id")}
        )
        response = self.client.put(
            url,
            constants.COMPLETE_SET_DIFFERENT_ID_UPDATE_FISH,
            format='json'
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        videos = Video.objects.all()
        self.assertEqual(len(videos), 1)
        self.assertEqual(len(videos[0].encoded_videos.all()), 2)
        first_url = videos[0].encoded_videos.all()[0].url
        self.assertEqual(
            first_url,
            constants.ENCODED_VIDEO_DICT_UPDATE_FISH_MOBILE.get("url")
        )
        second_url = videos[0].encoded_videos.all()[1].url
        self.assertEqual(
            second_url,
            constants.ENCODED_VIDEO_DICT_UPDATE_FISH_DESKTOP.get("url")
        )

    #Tests for bad PUT requests.

    def test_update_an_invalid_encoded_videos(self):
        """
        Tests PUTting one of two invalid EncodedVideo(s)
        """
        url = reverse('video-list')
        response = self.client.post(url, constants.COMPLETE_SET_FISH, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        url = reverse(
            'video-detail',
            kwargs={"edx_video_id": constants.COMPLETE_SET_FISH.get("edx_video_id")}
        )
        response = self.client.put(
            path=url,
            data=constants.COMPLETE_SET_INVALID_ENCODED_VIDEO_FISH,
            format='json'
        )
        self.assertEqual(
            response.data.get("encoded_videos")[1].get("profile")[0],
            "Object with profile_name=bird does not exist."
            )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        videos = Video.objects.all()
        self.assertEqual(len(videos), 1)
        self.assertEqual(len(videos[0].encoded_videos.all()), 2)
        first_url = videos[0].encoded_videos.all()[0].url
        self.assertEqual(
            first_url,
            constants.ENCODED_VIDEO_DICT_FISH_MOBILE.get("url")
        )
        second_url = videos[0].encoded_videos.all()[1].url
        self.assertEqual(
            second_url,
            constants.ENCODED_VIDEO_DICT_FISH_DESKTOP.get("url")
        )

    def test_update_duplicate_encoded_video_profiles(self):
        """
        Tests PUTting duplicate EncodedVideos for a Video
        """
        url = reverse('video-list')
        response = self.client.post(url, constants.COMPLETE_SET_FISH, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        url = reverse(
            'video-detail',
            kwargs={"edx_video_id": constants.COMPLETE_SET_FISH.get("edx_video_id")}
        )
        response = self.client.put(
            path=url,
            data=constants.COMPLETE_SET_TWO_MOBILE_FISH,
            format='json'
        )
        self.assertEqual(
            response.data.get("non_field_errors")[0],
            "Invalid data: duplicate profiles"
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        videos = Video.objects.all()
        self.assertEqual(len(videos), 1)
        self.assertEqual(len(videos[0].encoded_videos.all()), 2)
        first_url = videos[0].encoded_videos.all()[0].url
        self.assertEqual(
            first_url,
            constants.ENCODED_VIDEO_DICT_FISH_MOBILE.get("url")
        )
        second_url = videos[0].encoded_videos.all()[1].url
        self.assertEqual(
            second_url,
            constants.ENCODED_VIDEO_DICT_FISH_DESKTOP.get("url")
        )


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

    # Tests for successful POST 201 requests.
    def test_complete_set_two_encoded_video_post(self):
        """
        Tests POSTing Video and EncodedVideo pair
        """ #pylint: disable=R0801
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

    # Tests for 400_bad_request POSTs

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
    # Tests for POST queries to database

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


class VideoDetailTest(APITestCase):
    """
    Tests for GET
    """
    def setUp(self):
        """
        Used for manually creating profile objects which EncodedVideos require.
        """
        Profile.objects.create(**constants.PROFILE_DICT_MOBILE)
        Profile.objects.create(**constants.PROFILE_DICT_DESKTOP)

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
        """
        Tests number of queries when GETting all videos
        """
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
