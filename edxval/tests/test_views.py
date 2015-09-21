# pylint: disable=E1103, W0106
"""
Tests for Video Abstraction Layer views
"""
from django.core.urlresolvers import reverse
from rest_framework import status

from edxval.tests import constants, APIAuthTestCase
from edxval.models import Profile, Video, CourseVideo


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
        super(VideoDetail, self).setUp()

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
        response = self.client.patch(  # pylint: disable=E1101
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

    def test_update_remove_subtitles(self):
        # Create some subtitles
        self._create_videos(constants.COMPLETE_SET_STAR)

        # Sanity check that the subtitles have been created
        videos = Video.objects.all()
        self.assertEqual(len(videos), 1)
        self.assertEqual(len(videos[0].subtitles.all()), 1)

        # Update with an empty list of subtitles
        url = reverse(
            'video-detail',
            kwargs={"edx_video_id": constants.COMPLETE_SET_STAR.get("edx_video_id")}
        )
        response = self.client.put(
            url,
            dict(subtitles=[], encoded_videos=[], **constants.VIDEO_DICT_STAR),
            format='json'
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        # Expect that subtitles have been removed
        videos = Video.objects.all()
        self.assertEqual(len(videos), 1)
        self.assertEqual(len(videos[0].subtitles.all()), 0)

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
            constants.COMPLETE_SET_WITH_COURSE_KEY["courses"] +
            constants.COMPLETE_SET_WITH_OTHER_COURSE_KEYS["courses"]
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

    def _create_videos(self, data):
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
        super(VideoListTest, self).setUp()

    def tearDown(self):
        super(VideoListTest, self).tearDown()
        Video.objects.all().delete()

    # Tests for successful POST 201 requests.
    def test_complete_set_two_encoded_video_post(self):
        """
        Tests POSTing Video and EncodedVideo pair
        """  # pylint: disable=R0801
        url = reverse('video-list')
        response = self.client.post(
            url, constants.COMPLETE_SET_FISH, format='json'
        )
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        video = self.client.get("/edxval/videos/").data
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
            "This field must be unique."
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
        self.assertEqual(videos[0]['courses'], [course1, course2])

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
            'subtitles': [],
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


    # Tests for POST queries to database

    def test_queries_for_only_video(self):
        """
        Tests number of queries for a Video with no Encoded Videos
        """
        url = reverse('video-list')
        with self.assertNumQueries(9):
            self.client.post(url, constants.VIDEO_DICT_ZEBRA, format='json')

    def test_queries_for_two_encoded_video(self):
        """
        Tests number of queries for a Video/EncodedVideo(2) pair
        """
        url = reverse('video-list')
        with self.assertNumQueries(15):
            self.client.post(url, constants.COMPLETE_SET_FISH, format='json')

    def test_queries_for_single_encoded_videos(self):
        """
        Tests number of queries for a Video/EncodedVideo(1) pair
                """
        url = reverse('video-list')
        with self.assertNumQueries(13):
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
        super(VideoDetailTest, self).setUp()

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
        with self.assertNumQueries(9):
            self.client.get("/edxval/videos/").data
        response = self.client.post(url, constants.COMPLETE_SET_FISH, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        with self.assertNumQueries(12):
            self.client.get("/edxval/videos/").data
        response = self.client.post(url, constants.COMPLETE_SET_STAR, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        with self.assertNumQueries(14):
            self.client.get("/edxval/videos/").data


class SubtitleDetailTest(APIAuthTestCase):
    """
    Tests for subtitle API
    """
    def setUp(self):
        Profile.objects.create(profile_name=constants.PROFILE_MOBILE)
        Profile.objects.create(profile_name=constants.PROFILE_DESKTOP)
        super(SubtitleDetailTest, self).setUp()

    def test_get_subtitle_content(self):
        """
        Get subtitle content
        """
        url = reverse('video-list')
        response = self.client.post(
            url, constants.COMPLETE_SET_FISH, format='json'
        )
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        video = self.client.get("/edxval/videos/").data
        self.assertEqual(len(video), 1)
        self.assertEqual(len(video[0].get("subtitles")), 2)

        video_subtitles = video[0]['subtitles'][0]
        response = self.client.get(video_subtitles['content_url'])
        self.assertEqual(response.content, constants.SUBTITLE_DICT_SRT['content'])
        self.assertEqual(response['Content-Type'], 'text/plain')

        video_subtitles = video[0]['subtitles'][1]
        response = self.client.get(video_subtitles['content_url'])
        self.assertEqual(response.content, constants.SUBTITLE_DICT_SJSON['content'])
        self.assertEqual(response['Content-Type'], 'application/json')

    def test_update_subtitle(self):
        """
        Update an SRT subtitle
        """
        url = reverse('video-list')
        response = self.client.post(
            url, constants.COMPLETE_SET_FISH, format='json'
        )
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        video = response.data
        video_subtitles = video['subtitles'][0]
        url = reverse('subtitle-detail', kwargs={'video__edx_video_id': video['edx_video_id'], 'language': video_subtitles['language']})

        video_subtitles['content'] = 'testing 123'
        response = self.client.put(
            url, video_subtitles, format='json'
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(self.client.get(video_subtitles['content_url']).content, 'testing 123')

    def test_update_json_subtitle(self):
        """
        Update a JSON subtitle
        """
        url = reverse('video-list')
        response = self.client.post(
            url, constants.COMPLETE_SET_FISH, format='json'
        )
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        video = response.data
        video_subtitles = video['subtitles'][1]
        url = reverse('subtitle-detail', kwargs={'video__edx_video_id': video['edx_video_id'], 'language': video_subtitles['language']})

        video_subtitles['content'] = 'testing 123'
        response = self.client.put(
            url, video_subtitles, format='json'
        )
        # not in json format
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

        video_subtitles['content'] = """{"start": "00:00:00"

        }"""
        response = self.client.put(
            url, video_subtitles, format='json'
        )
        self.assertEqual(self.client.get(video_subtitles['content_url']).content, '{"start": "00:00:00"}')
