"""
Tests for Video Abstraction Layer views
"""


import json

from ddt import data, ddt, unpack
from django.urls import reverse
from rest_framework import status

from edxval.models import CourseVideo, EncodedVideo, Profile, TranscriptProviderType, Video, VideoTranscript
from edxval.serializers import TranscriptSerializer
from edxval.tests import APIAuthTestCase, constants
from edxval.utils import TranscriptFormat


class VideoDetail(APIAuthTestCase):
    """
    Tests Retrieve, Update and Destroy requests
    """

    def setUp(self):
        """
        Used for manually creating profile objects which EncodedVideos require.
        """
        Profile.objects.create(profile_name=constants.PROFILE_MOBILE)
        Profile.objects.create(profile_name=constants.PROFILE_DESKTOP)
        super().setUp()

    # Tests for successful PUT requests.

    def test_anonymous_denied(self):
        """
        Tests that reading/writing is not allowed for anonymous users.
        """
        self._logout()
        url = reverse('video-list')
        response = self.client.post(url, constants.VIDEO_DICT_ANIMAL, format='json')
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_no_perms(self):
        """
        Tests that reading/writing checks model permissions for logged in users.
        """
        self._logout()
        self._login(unauthorized=True)
        url = reverse('video-list')
        response = self.client.post(url, constants.VIDEO_DICT_ANIMAL, format='json')
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

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

    def test_update_three_encoded_videos(self):
        """
        Tests PUTting three encoded videos and then PUT back.
        """
        url = reverse('video-list')
        response = self.client.post(url, constants.COMPLETE_SET_FISH_WITH_HLS, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        url = reverse(
            'video-detail',
            kwargs={"edx_video_id": constants.COMPLETE_SET_FISH_WITH_HLS.get("edx_video_id")}
        )
        response = self.client.patch(
            path=url,
            data=constants.COMPLETE_SET_UPDATE_FISH,
            format='json'
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        videos = Video.objects.all()
        self.assertEqual(len(videos), 1)
        self.assertEqual(len(videos[0].encoded_videos.all()), 3)

        for index, encoding in enumerate(videos[0].encoded_videos.all()):
            before_update_encoding = constants.COMPLETE_SET_FISH_WITH_HLS['encoded_videos'][index]
            after_update_encoding = constants.COMPLETE_SET_UPDATE_FISH['encoded_videos'][index]

            self.assertNotEqual(
                before_update_encoding.get('url'),
                after_update_encoding.get('url')
            )
            self.assertEqual(
                encoding.url,
                after_update_encoding.get('url')
            )

        response = self.client.put(
            path=url,
            data=constants.COMPLETE_SET_FISH_WITH_HLS,
            format='json'
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        videos = Video.objects.all()
        self.assertEqual(len(videos), 1)
        self.assertEqual(len(videos[0].encoded_videos.all()), 3)

        for index, encoding in enumerate(videos[0].encoded_videos.all()):
            self.assertEqual(
                encoding.url,
                constants.COMPLETE_SET_FISH_WITH_HLS['encoded_videos'][index].get('url')
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

    def test_update_remove_encoded_videos(self):
        # Create some encoded videos
        self._create_videos(constants.COMPLETE_SET_STAR)

        # Sanity check that the encoded videos were created
        videos = Video.objects.all()
        self.assertEqual(len(videos), 1)
        self.assertEqual(len(videos[0].encoded_videos.all()), 1)

        # Update with an empty list of videos
        url = reverse(
            'video-detail',
            kwargs={"edx_video_id": constants.COMPLETE_SET_STAR.get("edx_video_id")}
        )
        response = self.client.put(
            url,
            dict(encoded_videos=[], **constants.VIDEO_DICT_STAR),
            format='json'
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        # Expect that encoded videos have been removed
        videos = Video.objects.all()
        self.assertEqual(len(videos), 1)
        self.assertEqual(len(videos[0].encoded_videos.all()), 0)

    def test_update_courses(self):
        # Create the video with associated course keys
        self._create_videos(constants.COMPLETE_SET_WITH_COURSE_KEY)

        # Verify that the video was associated with the courses
        video = Video.objects.get()
        course_keys = [c.course_id for c in CourseVideo.objects.filter(video=video)]
        self.assertEqual(course_keys, constants.COMPLETE_SET_WITH_COURSE_KEY["courses"])

        # Update the video to associate it with other courses
        url = reverse('video-detail', kwargs={"edx_video_id": video.edx_video_id})
        response = self.client.put(
            url,
            constants.COMPLETE_SET_WITH_OTHER_COURSE_KEYS,
            format='json'
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK, msg=response.content)

        # Verify that the video's courses were updated
        # Note: the current version of edx-val does NOT remove old course videos!
        course_keys = [c.course_id for c in CourseVideo.objects.filter(video=video)]
        expected_course_keys = (
            constants.COMPLETE_SET_WITH_COURSE_KEY["courses"] + constants.COMPLETE_SET_WITH_OTHER_COURSE_KEYS["courses"]
        )

        self.assertEqual(course_keys, expected_course_keys)

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

    # Tests for bad PUT requests.

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

    def _create_videos(self, data):  # pylint: disable=redefined-outer-name
        """
        Create videos for use in tests.
        """
        url = reverse('video-list')
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)


class VideoListTest(APIAuthTestCase):
    """
    Tests the creations of Videos via POST/GET
    """
    def setUp(self):
        """
        Used for manually creating profile objects which EncodedVideos require.
        """
        Profile.objects.create(profile_name=constants.PROFILE_MOBILE)
        Profile.objects.create(profile_name=constants.PROFILE_DESKTOP)
        super().setUp()

    def tearDown(self):
        super().tearDown()
        Video.objects.all().delete()

    # Tests for successful POST 201 requests.
    def test_complete_set_three_encoded_video_post(self):
        """
        Tests POSTing Video and EncodedVideo pair
        """
        url = reverse('video-list')
        response = self.client.post(
            url, constants.COMPLETE_SET_FISH_WITH_HLS, format='json'
        )
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        video = self.client.get("/edxval/videos/").data
        self.assertEqual(len(video), 1)
        self.assertEqual(len(video[0].get("encoded_videos")), 3)
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
        video = self.client.get("/edxval/videos/").data
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
        video = self.client.get("/edxval/videos/").data
        self.assertEqual(len(video), 1)
        self.assertEqual(len(video[0].get("encoded_videos")), 0)

    def test_post_video_invalid_course_key(self):
        """
        Tests POSTing a new Video with course video list containing some invalid course keys.
        """
        url = reverse('video-list')
        response = self.client.post(
            url, constants.COMPLETE_SET_WITH_SOME_INVALID_COURSE_KEY, format='json'
        )
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        response = json.loads(response.content.decode('utf-8'))
        # Check that invalid course keys have been filtered out.
        self.assertEqual(response['courses'], [{'edX/DemoX/Astonomy': None}])

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
        videos = len(self.client.get("/edxval/videos/").data)
        self.assertEqual(videos, 1)
        response = self.client.post(
            url, constants.VIDEO_DICT_ANIMAL, format='json'
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(
            response.data.get("edx_video_id")[0],
            'video with this edx video id already exists.'
        )
        videos = len(self.client.get("/edxval/videos/").data)
        self.assertEqual(videos, 1)

    def test_post_with_youtube(self):
        """
        Test that youtube is a valid profile.
        """
        url = reverse('video-list')

        video_data = dict(
            encoded_videos=[
                constants.ENCODED_VIDEO_DICT_FISH_MOBILE,
                constants.ENCODED_VIDEO_DICT_FISH_YOUTUBE
            ],
            **constants.VIDEO_DICT_FISH
        )
        response = self.client.post(
            url, video_data, format='json'
        )
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        videos = self.client.get("/edxval/videos/").data
        self.assertEqual(len(videos), 1)
        self.assertIn('youtube.com', videos[0]['encoded_videos'][1]['url'])

    def test_complete_set_invalid_encoded_video_post(self):
        """
        Tests POSTing valid Video and partial valid EncodedVideos.
        """
        url = reverse('video-list')
        response = self.client.post(
            url, constants.COMPLETE_SET_INVALID_ENCODED_VIDEO_FISH, format='json'
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        video = self.client.get("/edxval/videos/").data
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
        video = self.client.get("/edxval/videos/").data
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

    def test_add_course(self):
        """
        Test adding a video with a course.
        Test retrieving videos from course list view.
        """
        url = reverse('video-list')
        video = dict(**constants.VIDEO_DICT_ANIMAL)
        course1 = 'animals/fish/carp'
        course2 = 'animals/birds/cardinal'
        video['courses'] = [course1, course2]

        response = self.client.post(
            url, video, format='json'
        )
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        videos = self.client.get("/edxval/videos/").data
        self.assertEqual(len(videos), 1)
        self.assertEqual(videos[0]['courses'], [{course1: None}, {course2: None}])

        url = reverse('video-list') + '?course=%s' % course1
        videos = self.client.get(url).data
        self.assertEqual(len(videos), 1)
        self.assertEqual(videos[0]['edx_video_id'], constants.VIDEO_DICT_ANIMAL['edx_video_id'])

        url = reverse('video-list') + '?course=animals/fish/salmon'
        response = self.client.get(url).data
        self.assertEqual(len(response), 0)

    def test_lookup_youtube(self):
        """
        Test looking up by youtube id
        """
        video = {
            'edx_video_id': 'testing-youtube',
            'status': 'test',
            'encoded_videos': [
                {
                    'profile': 'youtube',
                    'url': 'AbcDef',
                    'file_size': 4545,
                    'bitrate': 6767,
                }
            ],
            'courses': ['youtube'],
            'client_video_id': "Funny Cats",
            'duration': 122
        }

        response = self.client.post(reverse('video-list'), video, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        # now look up the vid by youtube id
        url = reverse('video-list') + '?youtube=AbcDef'
        response = self.client.get(url).data
        self.assertEqual(len(response), 1)
        self.assertEqual(response[0]['edx_video_id'], video['edx_video_id'])

    def test_post_with_hls(self):
        """
        Test that hls is a valid profile.
        """
        url = reverse('video-list')

        video_data = dict(
            encoded_videos=[
                constants.ENCODED_VIDEO_DICT_FISH_HLS
            ],
            **constants.VIDEO_DICT_FISH
        )
        response = self.client.post(
            url, video_data, format='json'
        )
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        videos = self.client.get(url).data
        self.assertEqual(len(videos), 1)
        self.assertIn('https://www.tmnt.com/tmnt101.m3u8', videos[0]['encoded_videos'][0]['url'])

    # Tests for POST queries to database

    def test_queries_for_only_video(self):
        """
        Tests number of queries for a Video with no Encoded Videos
        """
        url = reverse('video-list')
        with self.assertNumQueries(8):
            self.client.post(url, constants.VIDEO_DICT_ZEBRA, format='json')

    def test_queries_for_two_encoded_video(self):
        """
        Tests number of queries for a Video/EncodedVideo(2) pair
        """
        url = reverse('video-list')
        with self.assertNumQueries(13):
            self.client.post(url, constants.COMPLETE_SET_FISH, format='json')

    def test_queries_for_single_encoded_videos(self):
        """
        Tests number of queries for a Video/EncodedVideo(1) pair
                """
        url = reverse('video-list')
        with self.assertNumQueries(11):
            self.client.post(url, constants.COMPLETE_SET_STAR, format='json')


class VideoDetailTest(APIAuthTestCase):
    """
    Tests for GET
    """
    def setUp(self):
        """
        Used for manually creating profile objects which EncodedVideos require.
        """
        Profile.objects.create(profile_name=constants.PROFILE_MOBILE)
        Profile.objects.create(profile_name=constants.PROFILE_DESKTOP)
        super().setUp()

    def test_get_all_videos(self):
        """
        Tests getting all Video objects
        """
        url = reverse('video-list')
        response = self.client.post(url, constants.VIDEO_DICT_ANIMAL, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        response = self.client.post(url, constants.VIDEO_DICT_ZEBRA, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        videos = self.client.get("/edxval/videos/").data
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
        with self.assertNumQueries(7):
            self.client.get("/edxval/videos/")
        response = self.client.post(url, constants.COMPLETE_SET_FISH, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        with self.assertNumQueries(9):
            self.client.get("/edxval/videos/")
        response = self.client.post(url, constants.COMPLETE_SET_STAR, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        with self.assertNumQueries(10):
            self.client.get("/edxval/videos/")


@ddt
class VideoImagesViewTest(APIAuthTestCase):
    """
    Tests VideoImage update requests.
    """

    def setUp(self):
        """
        Used for manually creating profile objects which EncodedVideos require.
        """
        self.course_id = 'test_course_id'
        self.video1 = Video.objects.create(**constants.VIDEO_DICT_FISH)
        self.video2 = Video.objects.create(**constants.VIDEO_DICT_DIFFERENT_ID_FISH)
        self.course_video1 = CourseVideo.objects.create(video=self.video1, course_id=self.course_id)
        self.course_video2 = CourseVideo.objects.create(video=self.video2, course_id=self.course_id)
        super().setUp()

    def test_update_auto_generated_images(self):
        """
        Tests POSTing generated images successfully.
        """
        generated_images = ['video-images/a.png', 'video-images/b.png', 'video-images/c.png']
        url = reverse('update-video-images')
        response = self.client.post(
            url,
            {
                'course_id': self.course_id,
                'edx_video_id': self.video1.edx_video_id,
                'generated_images': generated_images
            },
            format='json'
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(self.course_video1.video_image.image.name, generated_images[0])
        self.assertEqual(self.course_video1.video_image.generated_images, generated_images)

        # verify that if we post again then `VideoImage.image.name` should not be updated
        # but `VideoImage.generated_images` should be updated with new names.
        new_generated_images = ['a.png', 'b.png', 'c.png']
        response = self.client.post(
            url,
            {
                'course_id': self.course_id,
                'edx_video_id': self.video1.edx_video_id,
                'generated_images': new_generated_images
            },
            format='json'
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(self.course_video1.video_image.image.name, generated_images[0])
        course_video = CourseVideo.objects.get(video=self.video1, course_id=self.course_id)
        self.assertEqual(course_video.video_image.generated_images, new_generated_images)

    @data(
        {
            'post_data': {},
            'message': 'course_id and edx_video_id and generated_images must be specified to update a video image.'
        },
        {
            'post_data': {'course_id': 'does_not_exit_course', 'edx_video_id': 'super-soaker', 'generated_images': []},
            'message': 'CourseVideo not found for course_id: does_not_exit_course'
        },
        {
            'post_data': {'course_id': 'test_course_id', 'edx_video_id': 'does_not_exit_video', 'generated_images': []},
            'message': 'CourseVideo not found for course_id: test_course_id'
        },
        {
            'post_data': {'course_id': 'test_course_id', 'edx_video_id': 'super-soaker', 'generated_images': [1, 2, 3]},
            'message': "list must only contain strings.']"
        },
        {
            'post_data': {
                'course_id': 'test_course_id', 'edx_video_id': 'super-soaker', 'generated_images': [1, 2, 3, 4]
            },
            'message': "list must not contain more than 3 items.']"
        },
    )
    @unpack
    def test_update_error_responses(self, post_data, message):
        """
        Tests error responses occurred during POSTing.
        """
        url = reverse('update-video-images')

        response = self.client.post(url, post_data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn(
            message,
            response.data['message']
        )


@ddt
class VideoTranscriptViewTest(APIAuthTestCase):
    """
    Tests VideoTranscriptView.
    """

    def setUp(self):
        """
        Tests setup.
        """
        self.url = reverse('create-video-transcript')
        self.video = Video.objects.create(**constants.VIDEO_DICT_FISH)
        self.transcript_data = constants.VIDEO_TRANSCRIPT_CIELO24
        super().setUp()

    def test_create_transcript(self):
        """
        Tests POSTing transcript successfully.
        """
        post_transcript_data = dict(self.transcript_data)
        post_transcript_data.pop('file_data')
        post_transcript_data['name'] = post_transcript_data.pop('transcript')

        response = self.client.post(self.url, post_transcript_data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        serialized_data = TranscriptSerializer(VideoTranscript.objects.first()).data
        serialized_data['url'] = serialized_data['url'].lstrip('/')
        post_transcript_data['url'] = post_transcript_data.pop('name')
        self.assertDictEqual(serialized_data, post_transcript_data)

    def test_update_existing_transcript(self):
        """
        Tests updating existing transcript works as expected.
        """
        VideoTranscript.objects.create(
            video=self.video,
            language_code=self.transcript_data['language_code'],
            file_format=self.transcript_data['file_format'],
            provider=self.transcript_data['provider'],
        )

        post_transcript_data = dict(self.transcript_data)
        post_transcript_data['name'] = post_transcript_data.pop('transcript')

        response = self.client.post(self.url, post_transcript_data, format='json')

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(
            response.data['message'],
            'Can not override existing transcript for video "{video_id}" and language code "{language}".'.format(
                video_id=self.video.edx_video_id, language=post_transcript_data['language_code'])
        )

    @data(
        {
            'post_data': {},
            'message': 'video_id and name and language_code and provider and file_format must be specified.'
        },
        {
            'post_data': {
                'video_id': 'super-soaker',
                'name': 'abc.xyz',
                'language_code': 'en',
                'provider': TranscriptProviderType.CIELO24,
                'file_format': 'xyz'
            },
            'message': '"xyz" transcript file type is not supported. Supported formats are "{}"'.format(
                sorted(dict(TranscriptFormat.CHOICES).keys())
            )
        },
        {
            'post_data': {
                'video_id': 'super-soaker',
                'name': 'abc.srt',
                'language_code': 'en',
                'provider': 'xyz',
                'file_format': TranscriptFormat.SRT
            },
            'message': '"xyz" provider is not supported. Supported transcription providers are "{}"'.format(
                sorted(dict(TranscriptProviderType.CHOICES).keys())
            )
        },
    )
    @unpack
    def test_error_responses(self, post_data, message):
        """
        Tests error responses occurred during POSTing.
        """
        response = self.client.post(self.url, post_data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.data['message'], message)


@ddt
class VideoStatusViewTest(APIAuthTestCase):
    """
    VideoStatusView Tests.
    """
    def setUp(self):
        """
        Tests setup.
        """
        self.url = reverse('video-status-update')
        self.video = Video.objects.create(**constants.VIDEO_DICT_FISH)
        super().setUp()

    @data(
        {
            'patch_data': {},
            'message': '"edx_video_id and status" params must be specified.',
            'status_code': status.HTTP_400_BAD_REQUEST,
        },
        {
            'patch_data': {'edx_video_id': 'super-soaker', 'status': 'fake'},
            'message': '"fake" is not a valid Video status.',
            'status_code': status.HTTP_400_BAD_REQUEST,
        },
        {
            'patch_data': {'edx_video_id': 'fake', 'status': 'transcript_ready'},
            'message': 'Video is not found for specified edx_video_id: fake',
            'status_code': status.HTTP_400_BAD_REQUEST,
        },
        {
            'patch_data': {'edx_video_id': 'super-soaker', 'status': 'transcript_ready'},
            'message': None,
            'status_code': status.HTTP_200_OK,
        },
        {
            'patch_data': {'edx_video_id': 'super-soaker', 'status': 'transcode_active'},
            'message': None,
            'status_code': status.HTTP_200_OK,
        },
        {
            'patch_data': {'edx_video_id': 'super-soaker', 'status': 'file_complete'},
            'message': None,
            'status_code': status.HTTP_200_OK,
        },
        {
            'patch_data': {'edx_video_id': 'super-soaker', 'status': 'pipeline_error'},
            'message': None,
            'status_code': status.HTTP_200_OK,
        },
        {
            'patch_data': {'edx_video_id': 'super-soaker', 'status': 'partial_failure'},
            'message': None,
            'status_code': status.HTTP_200_OK,
        },
        {
            'patch_data': {'edx_video_id': 'super-soaker', 'status': 'transcript_failed'},
            'message': None,
            'status_code': status.HTTP_200_OK,
        }
    )
    @unpack
    def test_video_status(self, patch_data, message, status_code):
        """
        Tests PATCHing video status.
        """
        response = self.client.patch(self.url, patch_data, format='json')
        self.assertEqual(response.status_code, status_code)
        self.assertEqual(response.data.get('message'), message)

    def test_error_description(self):
        """
        Test that if error description is present in request, it is updated for
        the video instance.
        """
        request_data = {
            'edx_video_id': 'super-soaker', 'status': 'pipeline_error', 'error_description': 'test-error-desc'
        }
        response = self.client.patch(self.url, request_data, format='json')

        self.video.refresh_from_db()
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(self.video.error_description, 'test-error-desc')

    def test_no_error_description(self):
        """
        Test that error description is an optional parameter for status update request.
        """
        response = self.client.patch(
            self.url, {'edx_video_id': 'super-soaker', 'status': 'pipeline_error'}, format='json'
        )

        self.video.refresh_from_db()
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIsNone(self.video.error_description)


@ddt
class HLSMissingVideoViewTest(APIAuthTestCase):
    """
    HLSMissingVideoView Tests.
    """
    def setUp(self):
        """
        Tests setup.
        """
        self.url = reverse('hls-missing-video')

        desktop_profile, __ = Profile.objects.get_or_create(profile_name=constants.PROFILE_DESKTOP)
        hls_profile, __ = Profile.objects.get_or_create(profile_name=constants.PROFILE_HLS)

        # Setup 2 videos without hls profile
        video_wo_hls1 = Video.objects.create(**dict(
            constants.VIDEO_DICT_FISH, edx_video_id='video-wo-hls1', status='file_complete'
        ))
        video_wo_hls2 = Video.objects.create(**dict(
            constants.VIDEO_DICT_FISH, edx_video_id='video-wo-hls2', status='file_complete'
        ))
        EncodedVideo.objects.create(
            video=video_wo_hls1,
            profile=desktop_profile,
            **constants.ENCODED_VIDEO_DICT_DESKTOP
        )
        EncodedVideo.objects.create(
            video=video_wo_hls2,
            profile=desktop_profile,
            **constants.ENCODED_VIDEO_DICT_DESKTOP
        )

        # Setup 2 videos with hls profile
        video_w_hls1 = Video.objects.create(**dict(
            constants.VIDEO_DICT_FISH, edx_video_id='video-w-hls1', status='file_complete'
        ))
        video_w_hls2 = Video.objects.create(**dict(
            constants.VIDEO_DICT_FISH, edx_video_id='video-w-hls2', status='file_complete'
        ))
        EncodedVideo.objects.create(
            video=video_w_hls1,
            profile=hls_profile,
            **constants.ENCODED_VIDEO_DICT_HLS
        )
        EncodedVideo.objects.create(
            video=video_w_hls2,
            profile=hls_profile,
            **constants.ENCODED_VIDEO_DICT_HLS
        )

        # Put `video_wo_hls1` into two courses
        course_id1, course_id2 = 'test-course-1', 'test-course-2'
        CourseVideo.objects.create(video=video_wo_hls1, course_id=course_id1)
        CourseVideo.objects.create(video=video_wo_hls1, course_id=course_id2)

        super().setUp()

    @data(
        (1, 0),
        (2, 1),
        (2, 0),
        (2, 2),
    )
    @unpack
    def test_videos_list_missing_hls_encodes(self, batch_size, offset):
        """
        Test that videos that are missing HLS encodes are returned correctly.
        """
        expected_video_ids = ['video-wo-hls1', 'video-wo-hls2']
        response = self.client.post(self.url, {'batch_size': batch_size, 'offset': offset}, format='json')
        response = json.loads(response.content.decode('utf-8'))
        self.assertEqual(response['videos'], expected_video_ids[offset: offset + batch_size])

    def test_videos_list_missing_hls_encodes_for_courses(self):
        """
        Test that videos that are missing HLS encodes are returned correctly for the specified courses.
        """
        expected_video_ids = ['video-wo-hls1']
        response = self.client.post(self.url, {
            'courses': ['test-course-1', 'test-course-2']
        }, format='json')
        response = json.loads(response.content.decode('utf-8'))
        self.assertEqual(response['videos'], expected_video_ids)

    def test_update_hls_encodes_for_video(self):
        """
        Test that the encode profile gets updated successfully.
        """
        expected_data = {
            'edx_video_id': 'video-w-hls1',
            'profile': 'hls',
            'encode_data': {
                'file_size': 12,
                'bitrate': 12,
                'url': 'foo.com/abcd.m3u8'
            }
        }
        response = self.client.put(self.url, expected_data, format='json')
        # Assert the success response.
        self.assertEqual(response.status_code, 200)

        encoded_videos = EncodedVideo.objects.filter(
            video__edx_video_id=expected_data['edx_video_id'],
            profile__profile_name=expected_data['profile']
        )
        actual_encoded_video = encoded_videos.first()

        # Assert the updated profile and be sure its the only one.
        self.assertEqual(encoded_videos.count(), 1)
        self.assertEqual(actual_encoded_video.url, expected_data['encode_data']['url'])
        self.assertEqual(actual_encoded_video.file_size, expected_data['encode_data']['file_size'])
        self.assertEqual(actual_encoded_video.bitrate, expected_data['encode_data']['bitrate'])
