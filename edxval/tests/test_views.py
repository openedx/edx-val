from django.core.urlresolvers import reverse
from rest_framework import status
from rest_framework.test import APITestCase

from edxval.tests import constants
from edxval.models import Profile, Video
from edxval.serializers import EncodedVideoSetSerializer


class VideoListTest(APITestCase):
    """
    Tests the creations of Videos via POST/GET
    """
    def setUp(self):
        """
        SetUp
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
        url = reverse('video_view')
        response = self.client.post(
            url, constants.COMPLETE_SET_FISH, format='json'
        )
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        video = self.client.get("/edxval/video/").data
        self.assertEqual(len(video), 1)
        result = EncodedVideoSetSerializer(Video.objects.all()[0]).data
        self.assertEqual(len(result.get("encoded_videos")), 2)
        self.assertEqual(response.data, "Success")

    # def test_update_already_existing_complete_set(self):
    #     """
    #     Tests the update of an already existing Video and its EncodedVideos via POST
    #     """
    #     #TODO This test will fail until video/profile are unique_together
    #     #TODO and when profiles are updated instead of created
    #     url = reverse('video_view')
    #     response = self.client.post(
    #         url, constants.COMPLETE_SET_FISH, format='json'
    #     )
    #     self.assertEqual(response.status_code, status.HTTP_201_CREATED)
    #     response = self.client.post(
    #         url, constants.COMPLETE_SET_STAR, format='json'
    #     )
    #     video = self.client.get("/edxval/video/").data
    #     self.assertEqual(len(video), 1)
    #     result = EncodedVideoSetSerializer(Video.objects.all()[0]).data
    #     self.assertEqual(len(result.get("encoded_videos")), 2)
    #     self.assertEqual(response.data, "Success")

    def test_complete_set_with_extra_video_field(self):
        """
        Tests the case where there is an additional unneeded video field vis POST
        """
        url = reverse('video_view')
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
        Tests POSTing a new Video object
        """
        url = reverse('video_view')
        response = self.client.post(
            url, [constants.VIDEO_DICT_AVERAGE], format='json'
        )
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        result = EncodedVideoSetSerializer(Video.objects.all()[0]).data
        self.assertEqual(len(result.get("encoded_videos")), 0)

    def test_post_videos(self):
        """
        Tests POSTing same video
        """
        url = reverse('video_view')
        response = self.client.post(
            url, [constants.VIDEO_DICT_AVERAGE], format='json'
        )
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        videos = len(self.client.get("/edxval/video/").data)
        self.assertEqual(videos, 1)
        response = self.client.post(
            url, [constants.VIDEO_DICT_AVERAGE], format='json'
        )
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        videos = len(self.client.get("/edxval/video/").data)
        self.assertEqual(videos, 1)
        response = self.client.post(
            url, [constants.VIDEO_DICT_AVERAGE], format='json'
        )
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        videos = len(self.client.get("/edxval/video/").data)
        self.assertEqual(videos, 1)

    def test_post_multiple_valid_video_creation(self):
        """
        Tests POSTing than one valid videos

        Input is a list of video dicts
        """
        url = reverse('video_view')
        response = self.client.post(
            url, constants.VIDEO_DICT_SET_OF_THREE, format='json'
        )
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        videos = len(self.client.get("/edxval/video/").data)
        self.assertEqual(videos, 3)

    def test_post_valid_video_dict_list_duplicates(self):
        """
        Tests when POSTing valid duplicate dicts in a list
        """
        url = reverse('video_view')
        response = self.client.post(url, constants.VIDEO_DICT_DUPLICATES, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        videos = len(self.client.get("/edxval/video/").data)
        self.assertEqual(videos, 1)

    def test_post_non_latin_client_video_id(self):
        """
        Tests POSTing non-latin client_video_id
        """
        url = reverse('video_view')
        response = self.client.post(url, [constants.VIDEO_DICT_NON_LATIN_TITLE], format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

    def test_post_update_video(self):
        """
        Tests POST video update
        """
        url = reverse('video_view')
        response = self.client.post(url, [constants.VIDEO_DICT_AVERAGE], format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        response = self.client.post(url, [constants.VIDEO_DICT_AVERAGE2], format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        videos = self.client.get("/edxval/video/").data
        self.assertEqual(len(videos), 1)
        old_duration = constants.VIDEO_DICT_AVERAGE.get("duration")
        new_duration = videos[0].get("duration")
        self.assertNotEqual(new_duration, old_duration)
        old_client_video_id = constants.VIDEO_DICT_AVERAGE.get("client_video_id")
        new_client_video_id = videos[0].get("client_video_id")
        self.assertNotEqual(new_client_video_id, old_client_video_id)

    def test_post_an_encoded_video_for_different_video(self):
        """
        Tests POSTing encoded videos for different videos
        """
        url = reverse('video_view')
        response = self.client.post(
            url, constants.COMPLETE_SETS, format='json'
        )
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        videos = self.client.get("/edxval/video/").data
        self.assertEqual(len(videos), 2)
        self.assertNotEqual(videos[0], videos[1])

    """
    Tests for POSTing invalid data

    These tests should be returning HTTP_400_BAD_REQUEST
    """

    def test_complete_set_invalid_encoded_video_post(self):
        """
        Tests POSTing valid Video and partial valid EncodedVideos.
        """
        url = reverse('video_view')
        response = self.client.post(
            url, constants.COMPLETE_SET_INVALID_ENCODED_VIDEO_FISH, format='json'
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        video = self.client.get("/edxval/video/").data
        self.assertEqual(len(video), 1)
        result = EncodedVideoSetSerializer(Video.objects.all()[0]).data
        self.assertEqual(len(result.get("encoded_videos")), 0)
        self.assertIsNotNone(response.data.get("encoded_videos")[0])

    def test_complete_set_invalid_video_post(self):
        """
        Tests invalid Video POST
        """
        url = reverse('video_view')
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

    def test_complete_set_not_a_list(self):
        """
        Tests POST when the encoded videos are not a list of dicts
        """
        url = reverse('video_view')
        response = self.client.post(
            url, constants.COMPLETE_SET_NOT_A_LIST, format='json'
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(
            response.data,
            {'encoded_videos':[u"Expecting a list: <type 'dict'>"]}
        )

    def test_post_invalid_video_entry(self):
        """
        Tests for invalid video entry for POST
        """
        url = reverse('video_view')
        response = self.client.post(url, [constants.VIDEO_DICT_INVALID_ID], format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        errors = response.data
        self.assertEqual(
            errors[0].get("edx_video_id")[0],
            "edx_video_id has invalid characters"
        )

    def test_post_invalid_video_dict_list(self):
        """
        Tests POSTing a list of invalid Video dicts

        Input is a list of video dicts where [{valid},{invalid},{invalid}]
        """
        url = reverse('video_view')
        response = self.client.post(url, constants.VIDEO_DICT_INVALID_SET, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        errors = response.data
        self.assertEqual(
            errors[1].get("edx_video_id")[0],
            "edx_video_id has invalid characters"
        )
        self.assertEqual(
            errors[2].get("edx_video_id")[0],
            "edx_video_id has invalid characters"
        )
        videos = len(self.client.get("/edxval/video/").data)
        self.assertEqual(videos, 1)

    def test_post_non_latin_edx_video_id(self):
        """
        Tests POSTing non-latin edx_video_id
        """
        url = reverse('video_view')
        response = self.client.post(url, [constants.VIDEO_DICT_NON_LATIN_ID], format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_post_an_encoded_video_for_different_video(self):
        """
        Tests POSTing a list of Videos, [{valid}, {invalid}]
        """
        url = reverse('video_view')
        response = self.client.post(
            url, constants.COMPLETE_SETS_ONE_INVALID, format='json'
        )
        errors = response.data
        self.assertEqual(
            errors[1].get("edx_video_id")[0],
            "edx_video_id has invalid characters"
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        videos = self.client.get("/edxval/video/").data
        self.assertEqual(len(videos), 1)

    def test_post_all_invalid_videos(self):
        """
        Tests POSTing a list of Videos, [{invalid}, {invalid}]
        """
        url = reverse('video_view')
        response = self.client.post(
            url, constants.COMPLETE_SETS_ALL_INVALID, format='json'
        )
        errors = response.data
        self.assertEqual(
            errors[1].get("edx_video_id")[0],
            "edx_video_id has invalid characters"
        )
        self.assertEqual(
            errors[0].get("edx_video_id")[0],
            "edx_video_id has invalid characters"
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        videos = self.client.get("/edxval/video/").data
        self.assertEqual(len(videos), 0)

    """
    Tests for GET
    """
    def test_get_all_videos(self):
        """
        Tests getting all Video objects
        """
        url = reverse('video_view')
        response = self.client.post(url, [constants.VIDEO_DICT_AVERAGE], format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        response = self.client.post(url, [constants.VIDEO_DICT_COAT], format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        videos = len(self.client.get("/edxval/video/").data)
        self.assertEqual(videos, 2)