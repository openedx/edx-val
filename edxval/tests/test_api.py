# -*- coding: utf-8 -*-
"""
Tests for the API for Video Abstraction Layer
"""

import mock
from mock import patch
from lxml import etree

from django.test import TestCase
from django.db import DatabaseError
from django.core.urlresolvers import reverse
from rest_framework import status
from ddt import ddt, data

from edxval.models import Profile, Video, EncodedVideo, CourseVideo
from edxval import api as api
from edxval.api import (
    SortDirection,
    ValCannotCreateError,
    ValCannotUpdateError,
    ValVideoNotFoundError,
    VideoSortField,
)
from edxval.tests import constants, APIAuthTestCase


class SortedVideoTestMixin(object):
    """
    Test Mixin for testing api functions that sort the returned videos.
    """
    def _check_sort(self, api_func, sort_field, expected_ids_for_asc):
        """
        Assert that sorting by given field returns videos in the expected
        order (checking both ascending and descending)
        """
        def check_direction(sort_direction, expected_ids):
            """Assert that the given videos match the expected ids"""

            # Make sure it's not just returning the order given
            actual_videos = api_func(list(reversed(expected_ids)), sort_field, sort_direction)
            actual_ids = [video["edx_video_id"] for video in actual_videos]
            self.assertEqual(actual_ids, expected_ids)

        check_direction(SortDirection.asc, expected_ids_for_asc)
        check_direction(
            SortDirection.desc,
            list(reversed(expected_ids_for_asc))
        )

    def check_sort_params_of_api(self, api_func):
        """
        Verifies the given API function handles the sort parameters correctly for a list of videos.

        Args:
            api_func: A function with parameters (list-of-video-ids, sort_field, sort_direction)
                and returns a list of videos.
        """
        fish_id = constants.VIDEO_DICT_FISH["edx_video_id"]
        star_id = constants.VIDEO_DICT_STAR["edx_video_id"]
        other_id = "other-video"
        star_video = Video.objects.create(**constants.VIDEO_DICT_STAR)

        # This is made to sort with the other videos differently by each field
        other_video = Video.objects.create(
            client_video_id="other video",
            duration=555.0,
            edx_video_id=other_id
        )
        CourseVideo.objects.create(video=star_video, course_id=self.course_id)
        CourseVideo.objects.create(video=other_video, course_id=self.course_id)

        self._check_sort(api_func, VideoSortField.client_video_id, [fish_id, star_id, other_id])
        self._check_sort(api_func, VideoSortField.edx_video_id, [star_id, other_id, fish_id])
        # Check a field with a tie
        self._check_sort(api_func, VideoSortField.duration, [star_id, fish_id, other_id])


@ddt
class CreateVideoTest(TestCase):
    """
    Tests the create_video function in api.py.

    This function requires that a Profile object exist.
    """

    def setUp(self):
        """
        Creation of Profile objects that will be used to test video creation
        """
        api.create_profile(constants.PROFILE_DESKTOP)
        api.create_profile(constants.PROFILE_MOBILE)

    def test_create_video(self):
        """
        Tests the creation of a video
        """

        video_data = dict(
            encoded_videos=[
                constants.ENCODED_VIDEO_DICT_FISH_MOBILE
            ],
            **constants.VIDEO_DICT_FISH
        )
        result = api.create_video(video_data)
        videos = Video.objects.all()
        self.assertEqual(len(videos), 1)
        self.assertEqual("super-soaker", result)

    @data(
        constants.VIDEO_DICT_FISH,
        constants.VIDEO_DICT_NEGATIVE_DURATION,
        constants.VIDEO_DICT_INVALID_ID
    )
    def test_create_invalid_video(self, data): # pylint: disable=W0621
        """
        Tests the creation of a video with invalid data
        """
        with self.assertRaises(ValCannotCreateError):
            api.create_video(data)



@ddt
class UpdateVideoTest(TestCase):
    """
    Tests the update_video function in api.py.

    This function requires that a Video object exist.
    This function requires that a Profile object exist.
    """

    def setUp(self):
        """
        Creation of Video object that will be used to test video update
        Creation of Profile objects that will be used to test video update
        """
        api.create_profile(constants.PROFILE_DESKTOP)
        api.create_profile(constants.PROFILE_MOBILE)
        video_data = dict(
            encoded_videos=[
                constants.ENCODED_VIDEO_DICT_FISH_MOBILE
            ],
            **constants.VIDEO_DICT_FISH
        )
        api.create_video(video_data)


    def test_update_video(self):
        """
        Tests the update of a video
        """

        video_data = dict(
            encoded_videos=[
                constants.ENCODED_VIDEO_DICT_FISH_MOBILE
            ],
            **constants.VIDEO_DICT_FISH_UPDATE
        )
        result = api.update_video(video_data)
        videos = Video.objects.all()
        updated_video = videos[0]
        self.assertEqual(len(videos), 1)
        self.assertEqual(type(updated_video), Video)
        self.assertEqual(updated_video.client_video_id, "Full Swordfish")


    @data(
        constants.COMPLETE_SET_INVALID_ENCODED_VIDEO_FISH,
    )
    def test_update_video_incorrect_data(self, data):
        """
        Tests the update of a video with invalid data
        """
        with self.assertRaises(ValCannotUpdateError):
            api.update_video(data)


    @data(
        constants.VIDEO_DICT_DIFFERENT_ID_FISH
    )
    def test_update_video_not_found(self, data):
        """
        Tests the update of a video with invalid id
        """
        with self.assertRaises(ValVideoNotFoundError):
            api.update_video(data)


class CreateProfileTest(TestCase):
    """
    Tests the create_profile function in the api.py
    """

    def test_create_profile(self):
        """
        Tests the creation of a profile
        """
        api.create_profile(constants.PROFILE_DESKTOP)
        profiles = list(Profile.objects.all())
        self.assertEqual(len(profiles), 6)
        self.assertIn(
            constants.PROFILE_DESKTOP,
            [unicode(profile) for profile in profiles],
        )
        self.assertEqual(len(profiles), 6)

    def test_invalid_create_profile(self):
        """
        Tests the creation of invalid profile data
        """
        with self.assertRaises(ValCannotCreateError):
            api.create_profile(constants.PROFILE_INVALID_NAME)

    def test_create_profile_duplicate(self):
        api.create_profile(constants.PROFILE_DESKTOP)
        with self.assertRaises(ValCannotCreateError):
            api.create_profile(constants.PROFILE_DESKTOP)


class GetVideoInfoTest(TestCase):
    """
    Tests for our get_video_info function in api.py
    """

    def setUp(self):
        """
        Creates EncodedVideo objects in database
        """
        Profile.objects.create(profile_name=constants.PROFILE_MOBILE)
        Profile.objects.create(profile_name=constants.PROFILE_DESKTOP)
        video = Video.objects.create(**constants.VIDEO_DICT_FISH)
        EncodedVideo.objects.create(
            video=video,
            profile=Profile.objects.get(profile_name="mobile"),
            **constants.ENCODED_VIDEO_DICT_MOBILE
        )
        EncodedVideo.objects.create(
            video=video,
            profile=Profile.objects.get(profile_name="desktop"),
            **constants.ENCODED_VIDEO_DICT_DESKTOP
        )
        self.course_id = 'test-course'
        CourseVideo.objects.create(video=video, course_id=self.course_id)

    def test_get_video_found(self):
        """
        Tests for successful video request
        """
        self.assertIsNotNone(
            api.get_video_info(
                constants.VIDEO_DICT_FISH.get("edx_video_id")
            )
        )

    def test_no_such_video(self):
        """
        Tests searching for a video that does not exist
        """

        with self.assertRaises(api.ValVideoNotFoundError):
            api.get_video_info("non_existant-video__")
        with self.assertRaises(api.ValVideoNotFoundError):
            api.get_video_info("")

    def test_unicode_input(self):
        """
        Tests if unicode inputs are handled correctly
        """
        with self.assertRaises(api.ValVideoNotFoundError):
            api.get_video_info(u"๓ﻉѻฝ๓ٱซ")

    @mock.patch.object(Video, '__init__')
    def test_force_database_error(self, mock_get):
        """
        Tests to see if an database error will be handled
        """
        mock_get.side_effect = DatabaseError("DatabaseError")
        with self.assertRaises(api.ValInternalError):
            api.get_video_info(
                constants.VIDEO_DICT_FISH.get("edx_video_id")
            )


class GetUrlsForProfileTest(TestCase):
    """
    Tests the get_urls_for_profile(s) function in api.py
    """

    def setUp(self):
        """
        Creates EncodedVideo objects in database
        """
        Profile.objects.create(profile_name=constants.PROFILE_MOBILE)
        Profile.objects.create(profile_name=constants.PROFILE_DESKTOP)
        video = Video.objects.create(**constants.VIDEO_DICT_FISH)
        EncodedVideo.objects.create(
            video=Video.objects.get(
                edx_video_id=constants.VIDEO_DICT_FISH.get("edx_video_id")
            ),
            profile=Profile.objects.get(profile_name="mobile"),
            **constants.ENCODED_VIDEO_DICT_MOBILE
        )
        EncodedVideo.objects.create(
            video=Video.objects.get(
                edx_video_id=constants.VIDEO_DICT_FISH.get("edx_video_id")
            ),
            profile=Profile.objects.get(profile_name="desktop"),
            **constants.ENCODED_VIDEO_DICT_DESKTOP
        )
        self.course_id = 'test-course'
        CourseVideo.objects.create(video=video, course_id=self.course_id)

    def test_get_urls_for_profiles(self):
        """
        Tests when the profiles to the video are found
        """
        profiles = ["mobile", "desktop"]
        edx_video_id = constants.VIDEO_DICT_FISH['edx_video_id']
        urls = api.get_urls_for_profiles(edx_video_id, profiles)
        self.assertEqual(len(urls), 2)
        self.assertEqual(urls["mobile"], u'http://www.meowmix.com')
        self.assertEqual(urls["desktop"], u'http://www.meowmagic.com')

    def test_get_urls_for_profiles_no_video(self):
        """
        Tests when there is no video found.
        """
        urls = api.get_urls_for_profiles("not found", ["mobile"])
        self.assertEqual(urls["mobile"], None)

    def test_get_urls_for_profiles_no_profiles(self):
        """
        Tests when the video is found, but not hte profiles.
        """
        profiles = ["not", "found"]
        edx_video_id = constants.VIDEO_DICT_FISH['edx_video_id']
        urls = api.get_urls_for_profiles(edx_video_id, profiles)
        self.assertEqual(len(urls), 2)
        self.assertEqual(urls["not"], None)
        self.assertEqual(urls["found"], None)

    def test_get_url_for_profile(self):
        """
        Tests get_url_for_profile
        """
        profile = "mobile"
        edx_video_id = constants.VIDEO_DICT_FISH['edx_video_id']
        url = api.get_url_for_profile(edx_video_id, profile)
        self.assertEqual(url, u'http://www.meowmix.com')


class GetVideoForCourseProfiles(TestCase):
    """Tests get_video_info_for_course_and_profiles in api.py"""

    def setUp(self):
        """
        Creates two courses for testing

        Creates two videos with 2 encoded videos for the first course, and then
        2 videos with 1 encoded video for the second course.
        """
        mobile_profile = Profile.objects.create(profile_name=constants.PROFILE_MOBILE)
        desktop_profile = Profile.objects.create(profile_name=constants.PROFILE_DESKTOP)

        self.course_id = 'test-course'
        # 1st video
        video = Video.objects.create(**constants.VIDEO_DICT_FISH)
        EncodedVideo.objects.create(
            video=video,
            profile=mobile_profile,
            **constants.ENCODED_VIDEO_DICT_MOBILE
        )
        EncodedVideo.objects.create(
            video=video,
            profile=desktop_profile,
            **constants.ENCODED_VIDEO_DICT_DESKTOP
        )
        CourseVideo.objects.create(video=video, course_id=self.course_id)
        # 2nd video
        video = Video.objects.create(**constants.VIDEO_DICT_STAR)
        EncodedVideo.objects.create(
            video=video,
            profile=mobile_profile,
            **constants.ENCODED_VIDEO_DICT_MOBILE2
        )
        EncodedVideo.objects.create(
            video=video,
            profile=desktop_profile,
            **constants.ENCODED_VIDEO_DICT_DESKTOP2
        )
        CourseVideo.objects.create(video=video, course_id=self.course_id)

        self.course_id2 = "test-course2"
        # 3rd video different course
        video = Video.objects.create(**constants.VIDEO_DICT_TREE)
        EncodedVideo.objects.create(
            video=video,
            profile=mobile_profile,
            **constants.ENCODED_VIDEO_DICT_MOBILE3
        )
        CourseVideo.objects.create(video=video, course_id=self.course_id2)

        # 4th video different course
        video = Video.objects.create(**constants.VIDEO_DICT_PLANT)
        EncodedVideo.objects.create(
            video=video,
            profile=desktop_profile,
            **constants.ENCODED_VIDEO_DICT_DESKTOP3
        )
        CourseVideo.objects.create(video=video, course_id=self.course_id2)

    def _create_video_dict(self, video, encoding_dict):
        """
        Creates a video dict object from given constants
        """
        return {
            video['edx_video_id']: {
                "duration": video['duration'],
                'profiles': {
                    profile_name: {
                        "url": encoding["url"],
                        "file_size": encoding["file_size"],
                    }
                    for (profile_name, encoding) in encoding_dict.iteritems()
                }
            }
        }

    def test_get_video_for_course_profiles_success_one_profile(self):
        """
        Tests get_video_info_for_course_and_profiles for one profile
        """
        videos = api.get_video_info_for_course_and_profiles(
            self.course_id,
            ['mobile']
        )
        expected_dict = {}
        expected_dict.update(self._create_video_dict(
            constants.VIDEO_DICT_FISH,
            {
                constants.PROFILE_MOBILE: constants.ENCODED_VIDEO_DICT_MOBILE
            }
        ))
        expected_dict.update(self._create_video_dict(
            constants.VIDEO_DICT_STAR,
            {
                constants.PROFILE_MOBILE: constants.ENCODED_VIDEO_DICT_MOBILE2
            }))
        self.assertEqual(videos, expected_dict)

    def test_get_video_for_course_profiles_success_two_profiles(self):
        """
        Tests get_video_info_for_course_and_profiles for two profile
        """
        videos = api.get_video_info_for_course_and_profiles(
            'test-course',
            ['mobile', 'desktop'])
        expected_dict = {}
        expected_dict.update(self._create_video_dict(
            constants.VIDEO_DICT_FISH,
            {
                constants.PROFILE_MOBILE: constants.ENCODED_VIDEO_DICT_MOBILE,
                constants.PROFILE_DESKTOP: constants.ENCODED_VIDEO_DICT_DESKTOP,
            }
        ))
        expected_dict.update(self._create_video_dict(
            constants.VIDEO_DICT_STAR,
            {
                constants.PROFILE_MOBILE: constants.ENCODED_VIDEO_DICT_MOBILE2,
                constants.PROFILE_DESKTOP: constants.ENCODED_VIDEO_DICT_DESKTOP2,
            }
        ))
        self.assertEqual(videos, expected_dict)

    def test_get_video_for_course_profiles_no_profile(self):
        """Tests get_video_info_for_course_and_profiles with no such profile"""
        videos = api.get_video_info_for_course_and_profiles(
            'test-course',
            ['no_profile'])
        self.assertEqual(len(videos), 0)

        videos = api.get_video_info_for_course_and_profiles(
            'test-course',
            [])
        self.assertEqual(len(videos), 0)

        videos = api.get_video_info_for_course_and_profiles(
            'test-course',
            ['mobile', 'no_profile'])
        expected_dict = {}
        expected_dict.update(self._create_video_dict(
            constants.VIDEO_DICT_FISH,
            {
                constants.PROFILE_MOBILE: constants.ENCODED_VIDEO_DICT_MOBILE
            }
        ))
        expected_dict.update(self._create_video_dict(
            constants.VIDEO_DICT_STAR,
            {
                constants.PROFILE_MOBILE: constants.ENCODED_VIDEO_DICT_MOBILE2
            }
        ))
        self.assertEqual(videos, expected_dict)

    def test_get_video_for_course_profiles_video_with_one_profile(self):
        """
        Tests get_video_info_for_course_and_profiles with one of two profiles
        """
        videos = api.get_video_info_for_course_and_profiles(
            'test-course2',
            ['mobile'])
        expected_dict = {}
        expected_dict.update(self._create_video_dict(
            constants.VIDEO_DICT_TREE,
            {
                constants.PROFILE_MOBILE: constants.ENCODED_VIDEO_DICT_MOBILE3
            }
        ))
        self.assertEqual(videos, expected_dict)

        videos = api.get_video_info_for_course_and_profiles(
            'test-course2',
            ['desktop'])
        expected_dict = {}
        expected_dict.update(self._create_video_dict(
            constants.VIDEO_DICT_PLANT,
            {
                constants.PROFILE_DESKTOP: constants.ENCODED_VIDEO_DICT_DESKTOP3
            }
        ))
        self.assertEqual(videos, expected_dict)

    def test_get_video_for_course_profiles_repeated_profile(self):
        """
        Tests get_video_info_for_course_and_profiles with repeated profile
        """
        videos = api.get_video_info_for_course_and_profiles(
            'test-course',
            ['mobile', 'mobile'])
        expected_dict = {}
        expected_dict.update(self._create_video_dict(
            constants.VIDEO_DICT_FISH,
            {
                constants.PROFILE_MOBILE: constants.ENCODED_VIDEO_DICT_MOBILE,
            }
        ))
        expected_dict.update(self._create_video_dict(
            constants.VIDEO_DICT_STAR,
            {
                constants.PROFILE_MOBILE: constants.ENCODED_VIDEO_DICT_MOBILE2
            }
        ))
        self.assertEqual(videos, expected_dict)


class GetVideosForCourseTest(TestCase, SortedVideoTestMixin):
    """
    Tests for our get_videos_for_course function in api.py
    """

    def setUp(self):
        """
        Creates EncodedVideo objects in database
        """
        Profile.objects.create(profile_name=constants.PROFILE_MOBILE)
        Profile.objects.create(profile_name=constants.PROFILE_DESKTOP)

        # create video in the test course
        self.course_id = 'test-course'
        video = Video.objects.create(**constants.VIDEO_DICT_FISH)
        CourseVideo.objects.create(video=video, course_id=self.course_id)

        # create another video in a different course (to make sure it's not returned)
        video_in_other_course = Video.objects.create(
            client_video_id="video in another course",
            duration=111.0,
            edx_video_id="video-in-another-course",
        )
        CourseVideo.objects.create(video=video_in_other_course, course_id="other-course")

    def test_get_videos_for_course(self):
        """
        Tests retrieving videos for a course id
        """
        videos = list(api.get_videos_for_course(self.course_id))
        self.assertEqual(len(videos), 1)
        self.assertEqual(videos[0]['edx_video_id'], constants.VIDEO_DICT_FISH['edx_video_id'])
        videos = list(api.get_videos_for_course('unknown'))
        self.assertEqual(len(videos), 0)

    def test_get_videos_for_course_sort(self):
        """
        Tests retrieving videos for a course id according to sort
        """
        def api_func(_expected_ids, sort_field, sort_direction):
            return api.get_videos_for_course(
                self.course_id,
                sort_field,
                sort_direction,
            )
        self.check_sort_params_of_api(api_func)


class GetVideosForIdsTest(TestCase, SortedVideoTestMixin):
    """
    Tests the get_videos_for_ids function in api.py
    """

    def setUp(self):
        """
        Creates EncodedVideo objects in database
        """
        Profile.objects.create(profile_name=constants.PROFILE_MOBILE)
        Profile.objects.create(profile_name=constants.PROFILE_DESKTOP)
        video = Video.objects.create(**constants.VIDEO_DICT_FISH)
        EncodedVideo.objects.create(
            video=Video.objects.get(
                edx_video_id=constants.VIDEO_DICT_FISH.get("edx_video_id")
            ),
            profile=Profile.objects.get(profile_name="mobile"),
            **constants.ENCODED_VIDEO_DICT_MOBILE
        )
        EncodedVideo.objects.create(
            video=Video.objects.get(
                edx_video_id=constants.VIDEO_DICT_FISH.get("edx_video_id")
            ),
            profile=Profile.objects.get(profile_name="desktop"),
            **constants.ENCODED_VIDEO_DICT_DESKTOP
        )
        self.course_id = 'test-course'
        CourseVideo.objects.create(video=video, course_id=self.course_id)

    def test_get_videos_for_id(self):
        """
        Tests retrieving videos for id
        """
        edx_video_id = constants.VIDEO_DICT_FISH['edx_video_id']
        videos = list(api.get_videos_for_ids([edx_video_id]))
        self.assertEqual(len(videos), 1)
        self.assertEqual(videos[0]['edx_video_id'], edx_video_id)
        videos = list(api.get_videos_for_ids(['unknown']))
        self.assertEqual(len(videos), 0)

    def test_get_videos_for_ids(self):
        """
        Tests retrieving videos for ids
        """
        Video.objects.create(**constants.VIDEO_DICT_DIFFERENT_ID_FISH)
        EncodedVideo.objects.create(
            video=Video.objects.get(
                edx_video_id=constants.VIDEO_DICT_DIFFERENT_ID_FISH.get("edx_video_id")
            ),
            profile=Profile.objects.get(profile_name="mobile"),
            **constants.ENCODED_VIDEO_DICT_MOBILE
        )
        edx_video_id = constants.VIDEO_DICT_FISH['edx_video_id']
        edx_video_id_2 = constants.VIDEO_DICT_DIFFERENT_ID_FISH['edx_video_id']
        videos = list(api.get_videos_for_ids([edx_video_id, edx_video_id_2]))
        self.assertEqual(len(videos), 2)

    def test_get_videos_for_ids_duplicates(self):
        """
        Tests retrieving videos for ids when there are duplicate ids
        """
        edx_video_id = constants.VIDEO_DICT_FISH['edx_video_id']
        videos = list(api.get_videos_for_ids([edx_video_id, edx_video_id]))
        self.assertEqual(len(videos), 1)

    def test_get_videos_for_ids_sort(self):
        def api_func(expected_ids, sort_field, sort_direction):
            return api.get_videos_for_ids(
                expected_ids,
                sort_field,
                sort_direction,
            )
        self.check_sort_params_of_api(api_func)


class GetVideoInfoTestWithHttpCalls(APIAuthTestCase):
    """
    Tests for the get_info_video, using the HTTP requests to populate database
    """

    def setUp(self):
        """
        Creates EncodedVideo objects in database with HTTP requests.

        The tests are similar to the GetVideoInfoTest class. This class
        is to test that we have the same results, using a populated
        database via HTTP uploads.
        """
        super(GetVideoInfoTestWithHttpCalls, self).setUp()
        Profile.objects.create(profile_name=constants.PROFILE_MOBILE)
        Profile.objects.create(profile_name=constants.PROFILE_DESKTOP)
        url = reverse('video-list')
        response = self.client.post(
            url, constants.COMPLETE_SET_FISH, format='json'
        )
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

    def test_get_video_found(self):
        """
        Tests for successful video request
        """
        self.assertIsNotNone(
            api.get_video_info(
                constants.COMPLETE_SET_FISH.get("edx_video_id")
            )
        )

    def test_get_info_queries_for_two_encoded_video(self):
        """
        Tests number of queries for a Video/EncodedVideo(1) pair
        """
        with self.assertNumQueries(6):
            api.get_video_info(constants.COMPLETE_SET_FISH.get("edx_video_id"))

    def test_get_info_queries_for_one_encoded_video(self):
        """
        Tests number of queries for a Video/EncodedVideo(1) pair
        """
        url = reverse('video-list')
        response = self.client.post(
            url, constants.COMPLETE_SET_STAR, format='json'
        )
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        with self.assertNumQueries(5):
            api.get_video_info(constants.COMPLETE_SET_STAR.get("edx_video_id"))

    def test_get_info_queries_for_only_video(self):
        """
        Tests number of queries for a Video with no Encoded Videopair
        """
        url = reverse('video-list')
        response = self.client.post(
            url, constants.VIDEO_DICT_ZEBRA, format='json'
        )
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        with self.assertNumQueries(4):
            api.get_video_info(constants.VIDEO_DICT_ZEBRA.get("edx_video_id"))


class TestCopyCourse(TestCase):
    """Tests copy_course_videos in api.py"""

    def setUp(self):
        """
        Creates a course with 2 videos and a course with 1 video
        """
        self.course_id = 'test-course'
        # 1st video
        self.video1 = Video.objects.create(**constants.VIDEO_DICT_FISH)
        CourseVideo.objects.create(video=self.video1, course_id=self.course_id)
        # 2nd video
        self.video2 = Video.objects.create(**constants.VIDEO_DICT_STAR)
        CourseVideo.objects.create(video=self.video2, course_id=self.course_id)

        self.course_id2 = "test-course2"
        # 3rd video different course
        self.video3 = Video.objects.create(**constants.VIDEO_DICT_TREE)
        CourseVideo.objects.create(video=self.video3, course_id=self.course_id2)

    def test_successful_copy(self):
        """Tests a successful copy course"""
        api.copy_course_videos('test-course', 'course-copy1')
        original_videos = Video.objects.filter(courses__course_id='test-course')
        copied_videos = Video.objects.filter(courses__course_id='course-copy1')

        self.assertEqual(len(original_videos), 2)
        self.assertEqual(
            {original_video.edx_video_id for original_video in original_videos},
            {constants.VIDEO_DICT_FISH["edx_video_id"], constants.VIDEO_DICT_STAR["edx_video_id"]}
        )
        self.assertTrue(set(original_videos) == set(copied_videos))

    def test_same_course_ids(self):
        """
        Tests when the destination course id name is the same as the source
        """
        original_videos = Video.objects.filter(courses__course_id='test-course')
        api.copy_course_videos('test-course', 'test-course')
        copied_videos = Video.objects.filter(courses__course_id='test-course')
        self.assertEqual(len(original_videos), 2)
        self.assertTrue(set(original_videos) == set(copied_videos))

    def test_existing_destination_course_id(self):
        """Test when the destination course id already exists"""
        api.copy_course_videos('test-course', 'test-course2')
        original_videos = Video.objects.filter(courses__course_id='test-course')
        copied_videos = Video.objects.filter(courses__course_id='test-course2')
        self.assertEqual(len(original_videos), 2)
        self.assertLessEqual(set(original_videos), set(copied_videos))
        self.assertEqual(len(copied_videos), 3)

    def test_existing_video_in_destination_course_id(self):
        """
        Test when the destination course id already has videos from source id
        """
        course_id3 = 'test-course3'
        # 1st video
        CourseVideo.objects.create(video=self.video1, course_id=course_id3)

        api.copy_course_videos('test-course', 'test-course3')
        original_videos = Video.objects.filter(courses__course_id='test-course')
        copied_videos = Video.objects.filter(courses__course_id='test-course3')

        self.assertEqual(len(original_videos), 2)
        self.assertTrue(set(copied_videos) == set(original_videos))


class ExportTest(TestCase):
    """Tests export_to_xml"""
    def setUp(self):
        mobile_profile = Profile.objects.create(profile_name=constants.PROFILE_MOBILE)
        desktop_profile = Profile.objects.create(profile_name=constants.PROFILE_DESKTOP)
        Video.objects.create(**constants.VIDEO_DICT_STAR)
        video = Video.objects.create(**constants.VIDEO_DICT_FISH)
        EncodedVideo.objects.create(
            video=video,
            profile=mobile_profile,
            **constants.ENCODED_VIDEO_DICT_MOBILE
        )
        EncodedVideo.objects.create(
            video=video,
            profile=desktop_profile,
            **constants.ENCODED_VIDEO_DICT_DESKTOP
        )

    def assert_xml_equal(self, left, right):
        """
        Assert that the given XML fragments have the same attributes, text, and
        (recursively) children
        """
        def get_child_tags(elem):
            """Extract the list of tag names for children of elem"""
            return [child.tag for child in elem]

        for attr in ['tag', 'attrib', 'text', 'tail']:
            self.assertEqual(getattr(left, attr), getattr(right, attr))
        self.assertEqual(get_child_tags(left), get_child_tags(right))
        for left_child, right_child in zip(left, right):
            self.assert_xml_equal(left_child, right_child)

    def parse_xml(self, xml_str):
        """Parse XML for comparison with export output"""
        parser = etree.XMLParser(remove_blank_text=True)
        return etree.XML(xml_str, parser=parser)

    def test_no_encodings(self):
        expected = self.parse_xml("""
            <video_asset client_video_id="TWINKLE TWINKLE" duration="122.0"/>
        """)
        self.assert_xml_equal(
            api.export_to_xml(constants.VIDEO_DICT_STAR["edx_video_id"]),
            expected
        )

    def test_basic(self):
        expected = self.parse_xml("""
            <video_asset client_video_id="Shallow Swordfish" duration="122.0">
                <encoded_video url="http://www.meowmix.com" file_size="11" bitrate="22" profile="mobile"/>
                <encoded_video url="http://www.meowmagic.com" file_size="33" bitrate="44" profile="desktop"/>
            </video_asset>
        """)
        self.assert_xml_equal(
            api.export_to_xml(constants.VIDEO_DICT_FISH["edx_video_id"]),
            expected
        )

    def test_unknown_video(self):
        with self.assertRaises(ValVideoNotFoundError):
            api.export_to_xml("unknown_video")


@ddt
class ImportTest(TestCase):
    """Tests import_from_xml"""
    def setUp(self):
        mobile_profile = Profile.objects.create(profile_name=constants.PROFILE_MOBILE)
        Profile.objects.create(profile_name=constants.PROFILE_DESKTOP)
        video = Video.objects.create(**constants.VIDEO_DICT_FISH)
        EncodedVideo.objects.create(
            video=video,
            profile=mobile_profile,
            **constants.ENCODED_VIDEO_DICT_MOBILE
        )
        CourseVideo.objects.create(video=video, course_id='existing_course_id')

    def make_import_xml(self, video_dict, encoded_video_dicts=None):
        ret = etree.Element(
            "video_asset",
            attrib={
                key: unicode(video_dict[key])
                for key in ["client_video_id", "duration"]
            }
        )
        for encoding_dict in (encoded_video_dicts or []):
            etree.SubElement(
                ret,
                "encoded_video",
                attrib={
                    key: unicode(val)
                    for key, val in encoding_dict.items()
                }
            )
        return ret

    def assert_obj_matches_dict_for_keys(self, obj, dict_, keys):
        for key in keys:
            self.assertEqual(getattr(obj, key), dict_[key])

    def assert_video_matches_dict(self, video, video_dict):
        self.assert_obj_matches_dict_for_keys(
            video,
            video_dict,
            ["client_video_id", "duration"]
        )

    def assert_encoded_video_matches_dict(self, encoded_video, encoded_video_dict):
        self.assert_obj_matches_dict_for_keys(
            encoded_video,
            encoded_video_dict,
            ["url", "file_size", "bitrate"]
        )

    def assert_invalid_import(self, xml, course_id=None):
        edx_video_id = "test_edx_video_id"
        with self.assertRaises(ValCannotCreateError):
            api.import_from_xml(xml, edx_video_id, course_id)
        self.assertFalse(Video.objects.filter(edx_video_id=edx_video_id).exists())

    def test_new_video_full(self):
        new_course_id = "new_course_id"

        xml = self.make_import_xml(
            video_dict=constants.VIDEO_DICT_STAR,
            encoded_video_dicts=[constants.ENCODED_VIDEO_DICT_STAR]
        )
        api.import_from_xml(xml, constants.VIDEO_DICT_STAR["edx_video_id"], new_course_id)

        video = Video.objects.get(edx_video_id=constants.VIDEO_DICT_STAR["edx_video_id"])
        self.assert_video_matches_dict(video, constants.VIDEO_DICT_STAR)
        self.assert_encoded_video_matches_dict(
            video.encoded_videos.get(profile__profile_name=constants.PROFILE_MOBILE),
            constants.ENCODED_VIDEO_DICT_STAR
        )
        video.courses.get(course_id=new_course_id)

    def test_new_video_minimal(self):
        edx_video_id = "test_edx_video_id"

        xml = self.make_import_xml(
            video_dict={
                "client_video_id": "dummy",
                "duration": "0",
            }
        )
        api.import_from_xml(xml, edx_video_id)

        video = Video.objects.get(edx_video_id=edx_video_id)
        self.assertFalse(video.encoded_videos.all().exists())
        self.assertFalse(video.courses.all().exists())

    @data(
        # import into another course, where the video already exists, but is not associated with the course.
        "new_course_id",
        # re-import case, where the video and course association already exists.
        "existing_course_id"
    )
    def test_existing_video(self, course_id):
        xml = self.make_import_xml(
            video_dict={
                "client_video_id": "new_client_video_id",
                "duration": 0,
            },
            encoded_video_dicts=[
                constants.ENCODED_VIDEO_DICT_FISH_DESKTOP,
                {
                    "url": "http://example.com/new_url",
                    "file_size": 2733256,
                    "bitrate": 1597804,
                    "profile": "mobile",
                },
            ]
        )
        api.import_from_xml(xml, constants.VIDEO_DICT_FISH["edx_video_id"], course_id)

        video = Video.objects.get(edx_video_id=constants.VIDEO_DICT_FISH["edx_video_id"])
        self.assert_video_matches_dict(video, constants.VIDEO_DICT_FISH)
        self.assert_encoded_video_matches_dict(
            video.encoded_videos.get(profile__profile_name=constants.PROFILE_MOBILE),
            constants.ENCODED_VIDEO_DICT_MOBILE
        )
        self.assertFalse(
            video.encoded_videos.filter(profile__profile_name=constants.PROFILE_DESKTOP).exists()
        )
        self.assertTrue(video.courses.filter(course_id=course_id).exists())


    def test_existing_video_with_invalid_course_id(self):
        xml = self.make_import_xml(video_dict=constants.VIDEO_DICT_FISH)
        with self.assertRaises(ValCannotCreateError):
            api.import_from_xml(xml, edx_video_id=constants.VIDEO_DICT_FISH["edx_video_id"], course_id="x" * 300)

    def test_unknown_profile(self):
        profile = "unknown_profile"
        xml = self.make_import_xml(
            video_dict=constants.VIDEO_DICT_STAR,
            encoded_video_dicts=[
                constants.ENCODED_VIDEO_DICT_STAR,
                {
                    "url": "http://example.com/dummy",
                    "file_size": -1,  # Invalid data in an unknown profile is ignored
                    "bitrate": 0,
                    "profile": profile,
                }
            ]
        )
        api.import_from_xml(xml, constants.VIDEO_DICT_STAR["edx_video_id"])

        video = Video.objects.get(edx_video_id=constants.VIDEO_DICT_STAR["edx_video_id"])
        self.assertFalse(video.encoded_videos.filter(profile__profile_name=profile).exists())

    def test_invalid_tag(self):
        xml = etree.Element(
            "invalid_tag",
            attrib={
                "client_video_id": "dummy",
                "duration": "0",
            }
        )
        self.assert_invalid_import(xml)

    def test_invalid_video_attr(self):
        xml = self.make_import_xml(
            video_dict={
                "client_video_id": "dummy",
                "duration": -1,
            }
        )
        self.assert_invalid_import(xml)

    def test_invalid_encoded_video_attr(self):
        xml = self.make_import_xml(
            video_dict=constants.VIDEO_DICT_FISH,
            encoded_video_dicts=[{
                "url": "http://example.com/dummy",
                "file_size": -1,
                "bitrate": 0,
                "profile": "mobile"
            }]
        )
        self.assert_invalid_import(xml)

    def test_invalid_course_id(self):
        xml = self.make_import_xml(video_dict=constants.VIDEO_DICT_FISH)
        self.assert_invalid_import(xml, "x" * 300)


class GetCourseVideoRemoveTest(TestCase):
    """
    Tests to check `remove_video_for_course` function works correctly
    """

    def setUp(self):
        """
        Creates video objects for courses
        """
        # create video in the test course
        self.course_id = 'test-course'
        video = Video.objects.create(**constants.VIDEO_DICT_FISH)
        CourseVideo.objects.create(video=video, course_id=self.course_id)
        self.edx_video_id = video.edx_video_id

        # add the video in another course (to make sure that video is removed for correct course)
        CourseVideo.objects.create(video=video, course_id='other-course')

    def test_remove_video_for_course(self):
        """
        Tests video removal for a course
        """
        # we have one video for this course
        videos = list(api.get_videos_for_course(self.course_id))
        self.assertEqual(len(videos), 1)

        # remove the video and verify that video is removed from correct course
        api.remove_video_for_course(self.course_id, self.edx_video_id)
        videos = list(api.get_videos_for_course(self.course_id))
        self.assertEqual(len(videos), 0)

        # verify that CourseVideo related object exists(soft removal) for removed video
        course_video = CourseVideo.objects.get(course_id=self.course_id, video__edx_video_id=self.edx_video_id)
        self.assertEqual(course_video.is_hidden, True)

        # verify that video still exists for other course
        videos = list(api.get_videos_for_course('other-course'))
        self.assertEqual(len(videos), 1)

        # verify that video for other course has the correct info
        video_info = {key: videos[0][key] for key in constants.VIDEO_DICT_FISH}
        self.assertEqual(video_info, constants.VIDEO_DICT_FISH)


class VideoStatusUpdateTest(TestCase):
    """
    Tests to check video status update works correctly
    """
    @patch('edxval.models.logger')
    def test_video_instance_save_logging(self, mock_logger):
        """
        Tests correct message is logged when video instance is created and updated
        """
        video = Video.objects.create(**constants.VIDEO_DICT_FISH)
        mock_logger.info.assert_called_with(
            'VAL: Video created with id [%s] and status [%s]',
            video.edx_video_id,
            constants.VIDEO_DICT_FISH.get('status')
        )

        video.status = 'new_status'
        video.save()
        mock_logger.info.assert_called_with(
            'VAL: Status changed to [%s] for video [%s]',
            video.status,
            video.edx_video_id
        )

    @patch('edxval.models.logger')
    def test_update_video_status_logging(self, mock_logger):
        """
        Tests correct message is logged when `update_video_status` is called
        """
        video = Video.objects.create(**constants.VIDEO_DICT_FISH)
        api.update_video_status(video.edx_video_id, 'fail')
        mock_logger.info.assert_called_with(
            'VAL: Status changed to [%s] for video [%s]',
            'fail',
            video.edx_video_id
        )
