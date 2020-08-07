# -*- coding: utf-8 -*-
"""
Tests for the API for Video Abstraction Layer
"""


import copy
import json
import os
import shutil
from io import open
from tempfile import mkdtemp

import mock
from ddt import data, ddt, unpack
from django.conf import settings
from django.core.exceptions import ValidationError
from django.core.files import File
from django.core.files.base import ContentFile
from django.core.files.images import ImageFile
from django.db import DatabaseError
from django.test import TestCase
from django.urls import reverse
from fs.osfs import OSFS
from fs.path import combine
from lxml import etree
from mock import patch
from rest_framework import status

from edxval import api, utils
from edxval.api import (
    InvalidTranscriptFormat,
    InvalidTranscriptProvider,
    SortDirection,
    ValCannotCreateError,
    ValCannotUpdateError,
    ValVideoNotFoundError,
    VideoSortField,
)
from edxval.models import (
    LIST_MAX_ITEMS,
    CourseVideo,
    EncodedVideo,
    Profile,
    ThirdPartyTranscriptCredentialsState,
    TranscriptPreference,
    TranscriptProviderType,
    Video,
    VideoImage,
    VideoTranscript,
)
from edxval.serializers import VideoSerializer
from edxval.tests import APIAuthTestCase, constants
from edxval.transcript_utils import Transcript


def omit_attrs(dict, attrs_to_omit=None):  # pylint: disable=redefined-builtin
    """
    Omits provided attributes from the dict.
    """
    if attrs_to_omit is None:
        attrs_to_omit = []

    return {attr: value for attr, value in dict.items() if attr not in attrs_to_omit}


class SortedVideoTestMixin:
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
        super(CreateVideoTest, self).setUp()
        api.create_profile(constants.PROFILE_DESKTOP)
        api.create_profile(constants.PROFILE_MOBILE)

    def test_create_video(self):
        """
        Tests the creation of a video
        """

        video_data = dict(
            encoded_videos=[
                constants.ENCODED_VIDEO_DICT_FISH_MOBILE,
                constants.ENCODED_VIDEO_DICT_FISH_HLS
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
    def test_create_invalid_video(self, data):  # pylint: disable=W0621
        """
        Tests the creation of a video with invalid data
        """
        with self.assertRaises(ValCannotCreateError):
            api.create_video(data)

    def test_create_external_video(self):
        """
        Tests the creation of an external video.
        """
        expected_video = {
            'status': u'external',
            'client_video_id': u'Test Video',
            'duration': 0,
            'encoded_videos': [],
            'courses': []
        }
        edx_video_id = api.create_external_video(display_name=expected_video['client_video_id'])
        video = VideoSerializer(Video.objects.get(edx_video_id=edx_video_id)).data
        assert expected_video == {k: v for k, v in video.items() if k in expected_video}


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
        super(UpdateVideoTest, self).setUp()
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
        api.update_video(video_data)
        videos = Video.objects.all()
        updated_video = videos[0]
        self.assertEqual(len(videos), 1)
        self.assertEqual(type(updated_video), Video)
        self.assertEqual(updated_video.client_video_id, "Full Swordfish")

    @data(
        constants.COMPLETE_SET_INVALID_ENCODED_VIDEO_FISH,
    )
    def test_update_video_incorrect_data(self, data):  # pylint: disable=redefined-outer-name
        """
        Tests the update of a video with invalid data
        """
        with self.assertRaises(ValCannotUpdateError):
            api.update_video(data)

    @data(
        constants.VIDEO_DICT_DIFFERENT_ID_FISH
    )
    def test_update_video_not_found(self, data):  # pylint: disable=redefined-outer-name
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
        profile_names = [str(profile) for profile in profiles]
        self.assertEqual(len(profiles), 8)
        self.assertIn(
            constants.PROFILE_DESKTOP,
            profile_names
        )
        self.assertIn(
            constants.PROFILE_HLS,
            profile_names
        )
        self.assertIn(
            constants.PROFILE_AUDIO_MP3,
            profile_names
        )
        self.assertEqual(len(profiles), 8)

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


@ddt
class GetVideoInfoTest(TestCase):
    """
    Tests for our `get_video_info` and `is_video_available` methods in api.py
    """
    def setUp(self):
        """
        Creates EncodedVideo objects in database
        """
        super(GetVideoInfoTest, self).setUp()
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
        EncodedVideo.objects.create(
            video=video,
            profile=Profile.objects.get(profile_name="hls"),
            **constants.ENCODED_VIDEO_DICT_HLS
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

    @data(
        ('non-existent-edx-video-id', False),
        ('super-soaker', True)
    )
    @unpack
    def test_is_video_available(self, edx_video_id, expected_availability):
        """
        Tests to see if a video exists for an `edx_video_id`.
        """
        self.assertEqual(api.is_video_available(edx_video_id), expected_availability)


class GetUrlsForProfileTest(TestCase):
    """
    Tests the get_urls_for_profile(s) function in api.py
    """

    def setUp(self):
        """
        Creates EncodedVideo objects in database
        """
        super(GetUrlsForProfileTest, self).setUp()
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
        EncodedVideo.objects.create(
            video=Video.objects.get(
                edx_video_id=constants.VIDEO_DICT_FISH.get("edx_video_id")
            ),
            profile=Profile.objects.get(profile_name="hls"),
            **constants.ENCODED_VIDEO_DICT_HLS
        )
        self.course_id = 'test-course'
        CourseVideo.objects.create(video=video, course_id=self.course_id)

    def test_get_urls_for_profiles(self):
        """
        Tests when the profiles to the video are found
        """
        profiles = ["mobile", "desktop", 'hls']
        edx_video_id = constants.VIDEO_DICT_FISH['edx_video_id']
        urls = api.get_urls_for_profiles(edx_video_id, profiles)
        self.assertEqual(len(urls), 3)
        self.assertEqual(urls["mobile"], u'http://www.meowmix.com')
        self.assertEqual(urls["desktop"], u'http://www.meowmagic.com')
        self.assertEqual(urls["hls"], u'https://www.tmnt.com/tmnt101.m3u8')

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

        Creates two videos for first course where first video has 3 encodings and second
        video has 2 encoding and then 2 videos with 1 encoded video for the second course.
        """
        super(GetVideoForCourseProfiles, self).setUp()
        mobile_profile = Profile.objects.create(profile_name=constants.PROFILE_MOBILE)
        desktop_profile = Profile.objects.create(profile_name=constants.PROFILE_DESKTOP)
        hls_profile = Profile.objects.get(profile_name=constants.PROFILE_HLS)

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
        EncodedVideo.objects.create(
            video=video,
            profile=hls_profile,
            **constants.ENCODED_VIDEO_DICT_HLS
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
                    for (profile_name, encoding) in encoding_dict.items()
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

    def test_get_video_for_course_profiles_hls(self):
        """
        Tests get_video_info_for_course_and_profiles for hls profile
        """
        videos = api.get_video_info_for_course_and_profiles(
            self.course_id,
            ['hls']
        )
        self.assertEqual(
            videos,
            self._create_video_dict(
                constants.VIDEO_DICT_FISH,
                {
                    constants.PROFILE_HLS: constants.ENCODED_VIDEO_DICT_HLS
                }
            )
        )


class GetVideosForCourseTest(TestCase, SortedVideoTestMixin):
    """
    Tests for our get_videos_for_course function in api.py
    """

    def setUp(self):
        """
        Creates EncodedVideo objects in database
        """
        super(GetVideosForCourseTest, self).setUp()
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
        Tests retrieving all videos for a course id
        """
        videos, pagination_context = api.get_videos_for_course(self.course_id)
        videos = list(videos)
        self.assertEqual(len(videos), 1)
        self.assertEqual(pagination_context, {})
        self.assertEqual(videos[0]['edx_video_id'], constants.VIDEO_DICT_FISH['edx_video_id'])
        videos, __ = api.get_videos_for_course('unknown')
        videos = list(videos)
        self.assertEqual(len(videos), 0)

    def test_get_paginated_videos_for_course(self):
        """
        Test retrieving paginated videos for a course id
        """
        pagination_conf = {
            'page_number': 1,
            'videos_per_page': 1
        }
        videos, pagination_context = api.get_videos_for_course(
            self.course_id,
            pagination_conf=pagination_conf
        )
        videos = list(videos)
        self.assertEqual(len(videos), 1)
        self.assertNotEqual(pagination_context, {})

    def test_get_videos_for_course_sort(self):
        """
        Tests retrieving videos for a course id according to sort
        """
        def api_func(_expected_ids, sort_field, sort_direction):
            """ retrieving videos for a course id according to sort """
            videos, __ = api.get_videos_for_course(
                self.course_id,
                sort_field,
                sort_direction,
            )
            return videos
        self.check_sort_params_of_api(api_func)


@ddt
class GetYouTubeProfileVideosTest(TestCase):
    """
    Tests for get_course_video_ids_with_youtube_profile function in api.py
    """

    def setUp(self):
        """
        Creates two courses for testing

        Creates two videos with two encodings for first course
        and then two videos with one encoded video for the second course.
        """
        super(GetYouTubeProfileVideosTest, self).setUp()
        encodes = [
            dict(constants.ENCODED_VIDEO_DICT_YOUTUBE, profile=constants.PROFILE_YOUTUBE),
            dict(constants.ENCODED_VIDEO_DICT_DESKTOP, profile=constants.PROFILE_DESKTOP)
        ]
        self.video = Video.objects.create(**constants.VIDEO_DICT_FISH)
        for course_id in range(1, 3):
            self._setup_video_with_encodes_for_course(
                course_id='test-course' + str(course_id),
                video=self.video,
                encodes_data=copy.deepcopy(encodes)
            )

    def _setup_video_with_encodes_for_course(self, course_id, video, encodes_data):
        """ encoded videos for tests """
        for encode_data in encodes_data:
            profile, __ = Profile.objects.get_or_create(profile_name=encode_data.pop('profile'))
            EncodedVideo.objects.create(video=video, profile=profile, **encode_data)

        course_video = CourseVideo.objects.create(video=video, course_id=course_id)
        return course_video

    @data(
        ([], 2),
        (['test-course1'], 1),
        (['test-course2'], 1),
        (['test-course1', 'test-course2'], 2),
        (['test-course1', 'test-course2', 'test-course2'], 2)
    )
    @unpack
    def test_get_course_video_ids_with_youtube_profile_count(self, course_ids, count):
        """
        Tests count for course ids and video ids with youtube profile
        """
        ids = api.get_course_video_ids_with_youtube_profile(course_ids)
        self.assertEqual(len(ids), count)

    def test_get_course_video_ids_with_youtube_profile_content(self):
        """
        Tests content of course ids and video ids with youtube profile
        """
        ids = api.get_course_video_ids_with_youtube_profile(['test-course1'])
        self.assertEqual(ids, [('test-course1', 'super-soaker', 'https://www.youtube.com/watch?v=OscRe3pSP80')])

    def test_get_course_video_ids_with_youtube_profile_query_count(self):
        """
        Tests the query count for retrieving course ids and video ids with youtube profile
        """
        with self.assertNumQueries(3):
            api.get_course_video_ids_with_youtube_profile()


class GetVideosForIdsTest(TestCase, SortedVideoTestMixin):
    """
    Tests the get_videos_for_ids function in api.py
    """

    def setUp(self):
        """
        Creates EncodedVideo objects in database
        """
        super(GetVideosForIdsTest, self).setUp()
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
        """ Tests for videos """
        def api_func(expected_ids, sort_field, sort_direction):
            """ Tests for videos """
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
        with self.assertNumQueries(3):
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
        with self.assertNumQueries(3):
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
        with self.assertNumQueries(3):
            api.get_video_info(constants.VIDEO_DICT_ZEBRA.get("edx_video_id"))


class TestCopyCourse(TestCase):
    """Tests copy_course_videos in api.py"""

    def setUp(self):
        """
        Creates a course with 2 videos and a course with 1 video
        """
        super(TestCopyCourse, self).setUp()
        self.course_id = 'test-course'
        self.image_name1 = 'image.jpg'
        # 1st video
        self.video1 = Video.objects.create(**constants.VIDEO_DICT_FISH)
        self.course_video1 = CourseVideo.objects.create(video=self.video1, course_id=self.course_id)
        VideoImage.create_or_update(self.course_video1, self.image_name1)
        # 2nd video
        self.video2 = Video.objects.create(**constants.VIDEO_DICT_STAR)
        CourseVideo.objects.create(video=self.video2, course_id=self.course_id)

        self.course_id2 = "test-course2"
        # 3rd video different course
        self.video3 = Video.objects.create(**constants.VIDEO_DICT_TREE)
        CourseVideo.objects.create(video=self.video3, course_id=self.course_id2)

    def test_successful_copy(self):
        """
        Tests a successful copy course
        """
        destination_course_id = 'course-copy1'
        api.copy_course_videos(self.course_id, destination_course_id)
        original_videos = Video.objects.filter(courses__course_id=self.course_id)
        copied_videos = Video.objects.filter(courses__course_id=destination_course_id)
        course_video_with_image = CourseVideo.objects.get(video=self.video1, course_id=destination_course_id)
        course_video_without_image = CourseVideo.objects.get(video=self.video2, course_id=destination_course_id)

        self.assertEqual(len(original_videos), 2)
        self.assertEqual(
            {original_video.edx_video_id for original_video in original_videos},
            {constants.VIDEO_DICT_FISH["edx_video_id"], constants.VIDEO_DICT_STAR["edx_video_id"]}
        )
        self.assertEqual(set(original_videos), set(copied_videos))
        self.assertEqual(course_video_with_image.video_image.image.name, self.image_name1)
        self.assertFalse(hasattr(course_video_without_image, 'video_image'))

    def test_same_course_ids(self):
        """
        Tests when the destination course id name is the same as the source
        """
        original_videos = Video.objects.filter(courses__course_id='test-course')
        api.copy_course_videos('test-course', 'test-course')
        copied_videos = Video.objects.filter(courses__course_id='test-course')
        self.assertEqual(len(original_videos), 2)
        self.assertEqual(set(original_videos), set(copied_videos))

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
        self.assertEqual(set(copied_videos), set(original_videos))


@ddt
class ExportTest(TestCase):
    """
    Tests export_to_xml method.
    """
    def setUp(self):
        super(ExportTest, self).setUp()
        mobile_profile = Profile.objects.create(profile_name=constants.PROFILE_MOBILE)
        desktop_profile = Profile.objects.create(profile_name=constants.PROFILE_DESKTOP)
        hls_profile = Profile.objects.get(profile_name=constants.PROFILE_HLS)
        Video.objects.create(**constants.VIDEO_DICT_STAR)
        video = Video.objects.create(**constants.VIDEO_DICT_FISH)
        course_video = CourseVideo.objects.create(video=video, course_id='test-course')
        VideoImage.create_or_update(course_video, 'image.jpg')

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
        EncodedVideo.objects.create(
            video=video,
            profile=hls_profile,
            **constants.ENCODED_VIDEO_DICT_HLS
        )

        # create internal video transcripts
        transcript_data = dict(constants.VIDEO_TRANSCRIPT_CIELO24, video=video)
        transcript_data = omit_attrs(transcript_data, ['video_id', 'file_data'])
        VideoTranscript.objects.create(**transcript_data)
        transcript_data = dict(constants.VIDEO_TRANSCRIPT_3PLAY, video=video)
        transcript_data = omit_attrs(transcript_data, ['video_id', 'file_data'])
        VideoTranscript.objects.create(**transcript_data)

        self.temp_dir = mkdtemp()
        delegate_fs = OSFS(self.temp_dir)
        self.file_system = delegate_fs.makedir(constants.EXPORT_IMPORT_COURSE_DIR, recreate=True)
        self.file_system.makedir(constants.EXPORT_IMPORT_STATIC_DIR, recreate=True)
        self.addCleanup(shutil.rmtree, self.temp_dir)

    def assert_xml_equal(self, left, right):
        """
        Assert that the given XML fragments have the same attributes, text, and
        (recursively) children.
        """
        def get_child_tags(elem):
            """
            Extract the list of tag names for children of elem.
            """
            return [child.tag for child in elem]

        for attr in ['tag', 'attrib', 'text', 'tail']:
            self.assertEqual(getattr(left, attr), getattr(right, attr))
        self.assertEqual(get_child_tags(left), get_child_tags(right))
        for left_child, right_child in zip(left, right):
            self.assert_xml_equal(left_child, right_child)

    def parse_xml(self, xml_str):
        """
        Parse XML for comparison with export output.
        """
        parser = etree.XMLParser(remove_blank_text=True)
        return etree.XML(xml_str, parser=parser)

    def test_no_encodings(self):
        """
        Verify that transcript export for video with no encodings is working as expected.
        """
        expected = self.parse_xml("""
            <video_asset client_video_id="TWINKLE TWINKLE" duration="122.0" image=""/>
        """)
        exported_metadata = api.export_to_xml(
            resource_fs=self.file_system,
            static_dir=constants.EXPORT_IMPORT_STATIC_DIR,
            video_id=constants.VIDEO_DICT_STAR['edx_video_id'],
        )

        self.assert_xml_equal(exported_metadata['xml'], expected)

    def test_no_video_transcript(self):
        """
        Verify that transcript export for video with no transcript is working as expected.
        """
        expected = self.parse_xml("""
            <video_asset client_video_id="TWINKLE TWINKLE" duration="122.0" image=""/>
        """)

        exported_metadata = api.export_to_xml(
            constants.VIDEO_DICT_STAR['edx_video_id'],
            self.file_system,
            constants.EXPORT_IMPORT_STATIC_DIR
        )
        exported_xml = exported_metadata['xml']
        self.assert_xml_equal(exported_xml, expected)

        # Verify that no transcript is present in the XML.
        self.assertIsNone(exported_xml.attrib.get('transcripts'))

    @data(
        {'course_id': None, 'image': ''},
        {'course_id': 'test-course', 'image': 'image.jpg'},
    )
    @unpack
    def test_basic(self, course_id, image):
        """
        Test that video export works as expected.
        """
        expected = self.parse_xml("""
            <video_asset client_video_id="Shallow Swordfish" duration="122.0" image="{image}">
                <encoded_video url="http://www.meowmix.com" file_size="11" bitrate="22" profile="mobile"/>
                <encoded_video url="http://www.meowmagic.com" file_size="33" bitrate="44" profile="desktop"/>
                <encoded_video url="https://www.tmnt.com/tmnt101.m3u8" file_size="100" bitrate="0" profile="hls"/>
                <transcripts>
                    <transcript file_format="srt" language_code="de" provider="3PlayMedia" />
                    <transcript file_format="srt" language_code="en" provider="Cielo24" />
                </transcripts>
            </video_asset>
        """.format(image=image))

        exported_metadata = api.export_to_xml(
            constants.VIDEO_DICT_FISH['edx_video_id'],
            self.file_system,
            constants.EXPORT_IMPORT_STATIC_DIR,
            course_id
        )

        self.assert_xml_equal(exported_metadata['xml'], expected)
        self.assertEqual(sorted(exported_metadata['transcripts'].keys()), ['de', 'en'])

    def test_transcript_export(self):
        """
        Test that transcript are exported correctly.
        """
        language_code = 'en'
        video_id = constants.VIDEO_DICT_FISH['edx_video_id']
        transcript_files = {'de': u'super-soaker-de.srt', 'en': u'super-soaker-en.srt'}
        expected_transcript_path = combine(
            self.temp_dir,
            combine(constants.EXPORT_IMPORT_COURSE_DIR, constants.EXPORT_IMPORT_STATIC_DIR)
        )

        expected_xml = self.parse_xml("""
            <video_asset client_video_id="Shallow Swordfish" duration="122.0" image="image.jpg">
                <encoded_video url="http://www.meowmix.com" file_size="11" bitrate="22" profile="mobile"/>
                <encoded_video url="http://www.meowmagic.com" file_size="33" bitrate="44" profile="desktop"/>
                <encoded_video url="https://www.tmnt.com/tmnt101.m3u8" file_size="100" bitrate="0" profile="hls"/>
                <transcripts>
                    <transcript file_format="srt" language_code="de" provider="3PlayMedia" />
                    <transcript file_format="srt" language_code="en" provider="Cielo24" />
                </transcripts>
            </video_asset>
        """)

        exported_metadata = api.export_to_xml(
            video_id=video_id,
            course_id='test-course',
            resource_fs=self.file_system,
            static_dir=constants.EXPORT_IMPORT_STATIC_DIR
        )

        # Assert video and transcript xml is exported correctly.
        self.assert_xml_equal(exported_metadata['xml'], expected_xml)

        # Verify transcript file is created.
        self.assertEqual(
            sorted(transcript_files.values()),
            sorted(self.file_system.listdir(constants.EXPORT_IMPORT_STATIC_DIR))
        )

        # Also verify the content of created transcript file.
        for language_code in transcript_files.keys():  # pylint: disable=consider-iterating-dictionary
            expected_transcript_content = File(
                open(combine(expected_transcript_path, transcript_files[language_code]), 'rb')
            ).read()
            transcript = api.get_video_transcript_data(video_id=video_id, language_code=language_code)
            transcript_format = os.path.splitext(transcript['file_name'])[1][1:]
            exported_transcript_content = Transcript.convert(
                transcript['content'],
                input_format=transcript_format,
                output_format=Transcript.SRT,
            ).encode('utf-8')
            self.assertEqual(exported_transcript_content, expected_transcript_content)

    def test_unknown_video(self):
        """
        Test export with invalid video id.
        """
        with self.assertRaises(ValVideoNotFoundError):
            api.export_to_xml('unknown_video', self.file_system, constants.EXPORT_IMPORT_STATIC_DIR)


@ddt
class ImportTest(TestCase):
    """
    Tests import_from_xml
    """

    def setUp(self):
        super(ImportTest, self).setUp()
        self.image_name = 'image.jpg'
        mobile_profile = Profile.objects.create(profile_name=constants.PROFILE_MOBILE)
        Profile.objects.create(profile_name=constants.PROFILE_DESKTOP)
        video = Video.objects.create(**constants.VIDEO_DICT_FISH)
        EncodedVideo.objects.create(
            video=video,
            profile=mobile_profile,
            **constants.ENCODED_VIDEO_DICT_MOBILE
        )
        CourseVideo.objects.create(video=video, course_id='existing_course_id')

        self.transcript_data1 = dict(constants.VIDEO_TRANSCRIPT_CIELO24, video_id='little-star')
        self.transcript_data2 = dict(constants.VIDEO_TRANSCRIPT_3PLAY, video_id='little-star')
        self.transcript_data3 = dict(self.transcript_data2, video_id='super-soaker')

        self.temp_dir = mkdtemp()
        self.file_system = OSFS(self.temp_dir)
        self.file_system.makedir(constants.EXPORT_IMPORT_COURSE_DIR, recreate=True)
        self.file_system.makedir(
            constants.EXPORT_IMPORT_STATIC_DIR,
            recreate=True
        )

        self.addCleanup(shutil.rmtree, self.temp_dir)

    def make_import_xml(self, video_dict, encoded_video_dicts=None, image=None, video_transcripts=None):
        """ Importing xml"""
        import_xml = etree.Element(
            "video_asset",
            attrib={
                key: str(video_dict[key])
                for key in ["client_video_id", "duration"]
            }
        )

        if image:
            import_xml.attrib['image'] = image

        for encoding_dict in (encoded_video_dicts or []):
            etree.SubElement(
                import_xml,
                "encoded_video",
                attrib={
                    key: str(val)
                    for key, val in encoding_dict.items()
                }
            )

        if video_transcripts:
            transcripts_el = etree.SubElement(import_xml, 'transcripts')
            for video_transcript in video_transcripts:
                file_format = video_transcript['file_format']
                language_code = video_transcript['language_code']

                etree.SubElement(
                    transcripts_el,
                    'transcript',
                    {
                        'language_code': language_code,
                        'file_format': file_format,
                        'provider': video_transcript['provider'],
                    }
                )

                # Create transcript files
                transcript_file_name = u'{edx_video_id}-{language_code}.{file_format}'.format(
                    edx_video_id=video_dict['edx_video_id'],
                    language_code=language_code,
                    file_format=file_format
                )
                utils.create_file_in_fs(
                    video_transcript['file_data'],
                    transcript_file_name,
                    self.file_system,
                    constants.EXPORT_IMPORT_STATIC_DIR
                )

        return import_xml

    def assert_obj_matches_dict_for_keys(self, obj, dict_, keys):
        """ asserting dicts """
        for key in keys:
            self.assertEqual(getattr(obj, key), dict_[key])

    def assert_video_matches_dict(self, video, video_dict):
        """ asserting dicts """
        self.assert_obj_matches_dict_for_keys(
            video,
            video_dict,
            ["client_video_id", "duration"]
        )

    def assert_encoded_video_matches_dict(self, encoded_video, encoded_video_dict):
        """ asserting dicts """
        self.assert_obj_matches_dict_for_keys(
            encoded_video,
            encoded_video_dict,
            ["url", "file_size", "bitrate"]
        )

    def assert_invalid_import(self, xml, course_id=None):
        """ asserting dicts """
        edx_video_id = "test_edx_video_id"
        with self.assertRaises(ValCannotCreateError):
            api.import_from_xml(
                xml,
                edx_video_id,
                self.file_system,
                constants.EXPORT_IMPORT_STATIC_DIR,
                {},
                course_id
            )
        self.assertFalse(Video.objects.filter(edx_video_id=edx_video_id).exists())

    def assert_transcripts(self, video_id, expected_transcripts):
        """
        Compare `received` with `expected` and assert if not equal.
        """
        # Verify total number of expected transcripts for a video.
        video_transcripts = VideoTranscript.objects.filter(video__edx_video_id=video_id)
        self.assertEqual(video_transcripts.count(), len(expected_transcripts))

        # Verify data for each transcript.
        for expected_transcript in expected_transcripts:
            language_code = expected_transcript['language_code']

            # Get the imported transcript and remove `url` key.
            received_transcript = api.TranscriptSerializer(
                VideoTranscript.objects.get(video__edx_video_id=video_id, language_code=language_code)
            ).data

            # Assert transcript content
            received_transcript['file_data'] = api.get_video_transcript_data(
                video_id, language_code
            )['content'].decode('utf8')

            # Omit not needed attrs.
            expected_transcript = omit_attrs(expected_transcript, ['transcript'])
            received_transcript = omit_attrs(received_transcript, ['url'])

            self.assertDictEqual(received_transcript, expected_transcript)

    def test_new_video_full(self):
        new_course_id = 'new_course_id'

        xml = self.make_import_xml(
            video_dict=constants.VIDEO_DICT_STAR,
            encoded_video_dicts=[constants.ENCODED_VIDEO_DICT_STAR, constants.ENCODED_VIDEO_DICT_FISH_HLS],
            image=self.image_name,
            video_transcripts=[self.transcript_data1, self.transcript_data2]
        )

        # There must not be any transcript before import.
        self.assert_transcripts(constants.VIDEO_DICT_STAR['edx_video_id'], [])

        edx_video_id = api.import_from_xml(
            xml,
            constants.VIDEO_DICT_STAR['edx_video_id'],
            self.file_system,
            constants.EXPORT_IMPORT_STATIC_DIR,
            {},
            new_course_id
        )
        self.assertEqual(edx_video_id, constants.VIDEO_DICT_STAR['edx_video_id'])

        video = Video.objects.get(edx_video_id=constants.VIDEO_DICT_STAR['edx_video_id'])
        self.assert_video_matches_dict(video, constants.VIDEO_DICT_STAR)
        self.assert_encoded_video_matches_dict(
            video.encoded_videos.get(profile__profile_name=constants.PROFILE_MOBILE),
            constants.ENCODED_VIDEO_DICT_STAR
        )
        self.assert_encoded_video_matches_dict(
            video.encoded_videos.get(profile__profile_name=constants.PROFILE_HLS),
            constants.ENCODED_VIDEO_DICT_FISH_HLS
        )
        course_video = video.courses.get(course_id=new_course_id)
        self.assertTrue(course_video.video_image.image.name, self.image_name)

        self.assert_transcripts(
            constants.VIDEO_DICT_STAR['edx_video_id'],
            [self.transcript_data1, self.transcript_data2]
        )

    def test_new_video_minimal(self):
        edx_video_id = "test_edx_video_id"

        xml = self.make_import_xml(
            video_dict={
                "client_video_id": "dummy",
                "duration": "0",
            }
        )
        api.import_from_xml(xml, edx_video_id, self.file_system, constants.EXPORT_IMPORT_STATIC_DIR)

        video = Video.objects.get(edx_video_id=edx_video_id)
        self.assertFalse(video.encoded_videos.all().exists())
        self.assertFalse(video.courses.all().exists())

    @data(
        # import into another course, where the video already exists, but is not associated with the course.
        {'course_id': 'new_course_id', 'language_code': 'fr'},
        # re-import case, where the video and course association already exists.
        {'course_id': 'existing_course_id', 'language_code': 'nl'}
    )
    @unpack
    def test_existing_video(self, course_id, language_code):
        transcript_data = dict(self.transcript_data3, language_code=language_code)
        xml = self.make_import_xml(
            video_dict={
                'edx_video_id': constants.VIDEO_DICT_FISH['edx_video_id'],
                'client_video_id': 'new_client_video_id',
                'duration': 0,
            },
            encoded_video_dicts=[
                constants.ENCODED_VIDEO_DICT_FISH_DESKTOP,
                {
                    'url': 'http://example.com/new_url',
                    'file_size': 2733256,
                    'bitrate': 1597804,
                    'profile': 'mobile',
                },
            ],
            image=self.image_name,
            video_transcripts=[transcript_data]
        )

        # There must not be any transcript before import.
        self.assert_transcripts(constants.VIDEO_DICT_FISH['edx_video_id'], [])

        edx_video_id = api.import_from_xml(
            xml,
            constants.VIDEO_DICT_FISH['edx_video_id'],
            self.file_system,
            constants.EXPORT_IMPORT_STATIC_DIR,
            {},
            course_id
        )
        self.assertEqual(edx_video_id, constants.VIDEO_DICT_FISH['edx_video_id'])

        video = Video.objects.get(edx_video_id=constants.VIDEO_DICT_FISH['edx_video_id'])
        self.assert_video_matches_dict(video, constants.VIDEO_DICT_FISH)
        self.assert_encoded_video_matches_dict(
            video.encoded_videos.get(profile__profile_name=constants.PROFILE_MOBILE),
            constants.ENCODED_VIDEO_DICT_MOBILE
        )
        self.assertFalse(
            video.encoded_videos.filter(profile__profile_name=constants.PROFILE_DESKTOP).exists()
        )
        self.assertTrue(video.courses.filter(course_id=course_id).exists())
        course_video = video.courses.get(course_id=course_id)
        self.assertTrue(course_video.video_image.image.name, self.image_name)

        # Transcript is correctly imported when video already exists
        self.assert_transcripts(
            constants.VIDEO_DICT_FISH['edx_video_id'],
            [transcript_data],
        )

    def test_existing_video_with_invalid_course_id(self):
        xml = self.make_import_xml(video_dict=constants.VIDEO_DICT_FISH)
        with self.assertRaises(ValCannotCreateError):
            api.import_from_xml(
                xml,
                constants.VIDEO_DICT_FISH['edx_video_id'],
                self.file_system,
                constants.EXPORT_IMPORT_STATIC_DIR,
                {},
                course_id='x' * 300
            )

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
        api.import_from_xml(
            xml,
            constants.VIDEO_DICT_STAR['edx_video_id'],
            self.file_system,
            constants.EXPORT_IMPORT_STATIC_DIR
        )

        video = Video.objects.get(edx_video_id=constants.VIDEO_DICT_STAR['edx_video_id'])
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
        """
        Test the video xml import raises `ValCannotCreateError` on invalid course id.
        """
        xml = self.make_import_xml(
            video_dict=constants.VIDEO_DICT_FISH,
            encoded_video_dicts=[
                constants.ENCODED_VIDEO_DICT_STAR,
                constants.ENCODED_VIDEO_DICT_FISH_HLS
            ]
        )
        self.assert_invalid_import(xml, "x" * 300)

    def test_video_not_linked_to_course_if_no_encodes(self):
        """
        Test that an imported video is not linked to the corresponding course if it has no
        playable encodings.
        """
        course_id = 'existing_course_id'
        video_data = dict(constants.VIDEO_DICT_FISH, edx_video_id='video_with_no_encoding')

        xml = self.make_import_xml(
            video_dict=video_data,
            encoded_video_dicts=[]
        )

        api.import_from_xml(
            xml=xml,
            course_id=course_id,
            resource_fs=self.file_system,
            edx_video_id=video_data['edx_video_id'],
            static_dir=constants.EXPORT_IMPORT_STATIC_DIR,
        )

        # Assert that the video has been created and its status is external.
        video = Video.objects.get(edx_video_id=video_data['edx_video_id'])
        self.assertEqual(video.status, 'external')

        # Assert that the created video is not linked to any course
        with self.assertRaises(CourseVideo.DoesNotExist):
            CourseVideo.objects.get(video=video)

    def test_external_video_not_imported(self):
        """
        Verify that external videos are not imported into a course.
        """
        # Setup an external Video.
        Video.objects.create(**constants.EXTERNAL_VIDEO_DICT_FISH)
        xml = self.make_import_xml(video_dict=constants.EXTERNAL_VIDEO_DICT_FISH)
        api.import_from_xml(
            xml,
            constants.EXTERNAL_VIDEO_DICT_FISH['edx_video_id'],
            self.file_system,
            constants.EXPORT_IMPORT_STATIC_DIR,
            course_id='test_course_id'
        )
        # Assert that the existing video is not imported into the course.
        self.assertFalse(CourseVideo.objects.filter(
            course_id='test_course_id',
            video__edx_video_id=constants.EXTERNAL_VIDEO_DICT_FISH['edx_video_id']
        ).exists())

    def test_external_no_video_transcript(self):
        """
        Verify that transcript import for external video working as expected when there is no transcript.
        """
        api.import_from_xml(
            etree.fromstring('<video_asset/>'),
            '',
            self.file_system,
            constants.EXPORT_IMPORT_STATIC_DIR
        )
        self.assertEqual(
            VideoTranscript.objects.count(),
            0
        )

    @data(
        ('external-transcript.srt', constants.VIDEO_TRANSCRIPT_CUSTOM_SRT),
        ('external-transcript.sjson', constants.VIDEO_TRANSCRIPT_CUSTOM_SJSON)
    )
    @unpack
    def test_external_video_transcript(self, transcript_file_name, transcript_data):
        """
        Verify that transcript import for external video working as expected when there is transcript present.
        """
        # First create external transcript.
        utils.create_file_in_fs(
            transcript_data['file_data'],
            transcript_file_name,
            self.file_system,
            constants.EXPORT_IMPORT_STATIC_DIR
        )

        # Verify that one video is present before import.
        self.assertEqual(Video.objects.count(), 1)

        # Verify that no transript was present before import.
        self.assertEqual(VideoTranscript.objects.count(), 0)

        # Import xml with empty edx video id.
        edx_video_id = api.import_from_xml(
            etree.fromstring('<video_asset/>'),
            '',
            self.file_system,
            constants.EXPORT_IMPORT_STATIC_DIR,
            {
                'en': [transcript_file_name]
            }
        )

        # Verify that a new video is created.
        self.assertIsNotNone(edx_video_id)

        # Verify transcript record is created with correct data.
        self.assert_transcripts(
            edx_video_id,
            [dict(transcript_data, video_id=edx_video_id)]
        )

    def test_multiple_external_transcripts_different_langauges(self):
        """
        Verify that transcript import for external video working as expected when multiple transcripts are imported.
        """
        # First create external transcripts.
        en_transcript_file_name = 'external-transcript-en.srt'
        utils.create_file_in_fs(
            constants.VIDEO_TRANSCRIPT_CUSTOM_SRT['file_data'],
            en_transcript_file_name,
            self.file_system,
            constants.EXPORT_IMPORT_STATIC_DIR
        )

        es_transcript_file_name = 'external-transcript-es.srt'
        utils.create_file_in_fs(
            constants.VIDEO_TRANSCRIPT_CUSTOM_SRT['file_data'],
            es_transcript_file_name,
            self.file_system,
            constants.EXPORT_IMPORT_STATIC_DIR
        )

        # Verify that one video is present before import.
        self.assertEqual(Video.objects.count(), 1)

        # Verify that no transript was present before import.
        self.assertEqual(VideoTranscript.objects.count(), 0)

        # Import xml with empty edx video id.
        edx_video_id = api.import_from_xml(
            etree.fromstring('<video_asset/>'),
            '',
            self.file_system,
            constants.EXPORT_IMPORT_STATIC_DIR,
            {
                'en': [en_transcript_file_name],
                'es': [es_transcript_file_name]
            }
        )

        # Verify that new video is created.
        self.assertIsNotNone(edx_video_id)

        # Verify transcript records are created with correct data.
        expected_transcripts = [
            dict(constants.VIDEO_TRANSCRIPT_CUSTOM_SRT, video_id=edx_video_id, language_code='en'),
            dict(constants.VIDEO_TRANSCRIPT_CUSTOM_SRT, video_id=edx_video_id, language_code='es')
        ]

        self.assert_transcripts(
            edx_video_id,
            expected_transcripts
        )

    def test_multiple_external_transcripts_for_language(self):
        """
        Verify that transcript import for external video working as expected when multiple transcripts present against
        a language e.g. external english transcript is imported through sub and transcripts field.
        """
        # First create external transcripts.
        sub_transcript_file_name = 'external-transcript-sub.srt'
        utils.create_file_in_fs(
            constants.VIDEO_TRANSCRIPT_CUSTOM_SRT['file_data'],
            sub_transcript_file_name,
            self.file_system,
            constants.EXPORT_IMPORT_STATIC_DIR
        )

        ext_transcript_file_name = 'external-transcript-ext.sjson'
        utils.create_file_in_fs(
            constants.VIDEO_TRANSCRIPT_CUSTOM_SJSON['file_data'],
            ext_transcript_file_name,
            self.file_system,
            constants.EXPORT_IMPORT_STATIC_DIR
        )

        # Verify that one video is present before import.
        self.assertEqual(Video.objects.count(), 1)

        # Verify that no transript was present before import.
        self.assertEqual(VideoTranscript.objects.count(), 0)

        # Import xml with empty edx video id.
        edx_video_id = api.import_from_xml(
            etree.fromstring('<video_asset/>'),
            '',
            self.file_system,
            constants.EXPORT_IMPORT_STATIC_DIR,
            {
                'en': [sub_transcript_file_name, ext_transcript_file_name]
            }
        )

        # Verify that new video is created.
        self.assertIsNotNone(edx_video_id)

        # Verify transcript record is created with correct data i.e sub field transcript.
        expected_transcripts = [
            dict(constants.VIDEO_TRANSCRIPT_CUSTOM_SRT, video_id=edx_video_id, language_code='en')
        ]

        self.assert_transcripts(
            edx_video_id,
            expected_transcripts
        )

    def test_external_internal_transcripts_conflict(self):
        """
        Tests that when importing both external and internal (VAL) transcripts, internal transcript is imported.
        """
        # First create external transcript in sjson format.
        en_transcript_file_name = 'external-transcript-en.sjson'
        utils.create_file_in_fs(
            constants.VIDEO_TRANSCRIPT_CUSTOM_SJSON['file_data'],
            en_transcript_file_name,
            self.file_system,
            constants.EXPORT_IMPORT_STATIC_DIR
        )

        # Let's create internal transcript in srt format.
        expected_val_transcript = [self.transcript_data1]
        import_xml = self.make_import_xml(
            video_dict=constants.VIDEO_DICT_STAR,
            video_transcripts=expected_val_transcript
        )

        # Verify that one video is present before import.
        self.assertEqual(Video.objects.count(), 1)

        # Verify that no transript was present before import.
        self.assertEqual(VideoTranscript.objects.count(), 0)

        # Note that we have an external en transcript as well as internal en transcript.
        edx_video_id = api.import_from_xml(
            import_xml,
            constants.VIDEO_DICT_STAR['edx_video_id'],
            self.file_system,
            constants.EXPORT_IMPORT_STATIC_DIR,
            {
                'en': [en_transcript_file_name]
            }
        )

        # Verify that new video is created.
        self.assertIsNotNone(edx_video_id)

        # Verify transcript record is created with internal transcript data.
        self.assert_transcripts(
            constants.VIDEO_DICT_STAR['edx_video_id'],
            [self.transcript_data1]
        )

    def test_external_internal_transcripts_different_languages(self):
        """
        Tests that when importing both external and internal (VAL) transcripts for different langauges, all transcripts
        are imported correctly.
        """
        edx_video_id = constants.VIDEO_DICT_STAR['edx_video_id']
        # First create external es transcript.
        es_transcript_file_name = 'external-transcript-es.sjson'
        es_external_transcript = dict(
            constants.VIDEO_TRANSCRIPT_CUSTOM_SJSON,
            video_id=edx_video_id,
            language_code='es'
        )
        utils.create_file_in_fs(
            es_external_transcript['file_data'],
            es_transcript_file_name,
            self.file_system,
            constants.EXPORT_IMPORT_STATIC_DIR
        )

        # Let's create en internal transcript.
        import_xml = self.make_import_xml(
            video_dict=constants.VIDEO_DICT_STAR,
            video_transcripts=[self.transcript_data1]
        )

        # Verify that one video is present before import.
        self.assertEqual(Video.objects.count(), 1)

        # Verify that no transript was present before import.
        self.assertEqual(VideoTranscript.objects.count(), 0)

        # Note that we have an external 'es' language transcript as well as an internal 'es' language transcript.
        edx_video_id = api.import_from_xml(
            import_xml,
            edx_video_id,
            self.file_system,
            constants.EXPORT_IMPORT_STATIC_DIR,
            {
                'es': [es_transcript_file_name]
            }
        )

        # Verify all transcript records are created correctly.
        self.assert_transcripts(
            constants.VIDEO_DICT_STAR['edx_video_id'],
            [self.transcript_data1, es_external_transcript]
        )

    @patch('edxval.api.logger')
    def test_import_transcript_from_fs_resource_not_found(self, mock_logger):
        """
        Test that `import_transcript_from_fs` correctly logs if transcript file is not found in file system.
        """
        language_code = 'en'
        edx_video_id = 'test-edx-video-id'
        file_name = 'file-not-found.srt'
        api.import_transcript_from_fs(
            edx_video_id=edx_video_id,
            language_code=language_code,
            file_name=file_name,
            provider=TranscriptProviderType.CUSTOM,
            resource_fs=self.file_system,
            static_dir=constants.EXPORT_IMPORT_STATIC_DIR
        )
        mock_logger.warning.assert_called_with(
            '[edx-val] "%s" transcript "%s" for video "%s" is not found.',
            language_code,
            file_name,
            edx_video_id
        )

    @patch('edxval.api.logger')
    def test_import_transcript_from_fs_invalid_format(self, mock_logger):
        """
        Test that `import_transcript_from_fs` correctly logs if we get error while retrieving transcript file format.
        """
        language_code = 'en'
        edx_video_id = constants.VIDEO_DICT_FISH['edx_video_id']
        # First create transcript file.
        invalid_transcript_file_name = 'invalid-transcript.txt'
        invalid_transcript = dict(
            constants.VIDEO_TRANSCRIPT_CUSTOM_SJSON,
            video_id=edx_video_id,
            file_data='This is an invalid transcript file data.'
        )
        utils.create_file_in_fs(
            invalid_transcript['file_data'],
            invalid_transcript_file_name,
            self.file_system,
            constants.EXPORT_IMPORT_STATIC_DIR
        )

        api.import_transcript_from_fs(
            edx_video_id=edx_video_id,
            language_code=language_code,
            file_name=invalid_transcript_file_name,
            provider=TranscriptProviderType.CUSTOM,
            resource_fs=self.file_system,
            static_dir=constants.EXPORT_IMPORT_STATIC_DIR
        )
        mock_logger.warning.assert_called_with(
            '[edx-val] Error while getting transcript format for video=%s -- language_code=%s --file_name=%s',
            edx_video_id,
            language_code,
            invalid_transcript_file_name
        )

    @patch('edxval.api.logger')
    def test_import_transcript_from_fs_bad_content(self, mock_logger):
        """
        Test that `import_transcript_from_fs` correctly logs if we get error while decoding transcript content.
        """
        language_code = 'en'
        edx_video_id = constants.VIDEO_DICT_FISH['edx_video_id']

        # First create non utf-8 encoded transcript file in the file system.
        transcript_file_name = 'invalid-transcript.txt'
        invalid_transcript = dict(
            constants.VIDEO_TRANSCRIPT_CUSTOM_SJSON,
            video_id=edx_video_id,
            file_data=u'Привіт, edX вітає вас.'
        )

        with self.file_system.open(combine(constants.EXPORT_IMPORT_STATIC_DIR, transcript_file_name), 'wb') as f:
            f.write(invalid_transcript['file_data'].encode('cp1251'))

        api.import_transcript_from_fs(
            edx_video_id=edx_video_id,
            language_code=language_code,
            file_name=transcript_file_name,
            provider=TranscriptProviderType.CUSTOM,
            resource_fs=self.file_system,
            static_dir=constants.EXPORT_IMPORT_STATIC_DIR
        )
        mock_logger.warning.assert_called_with(
            '[edx-val] "%s" transcript "%s" for video "%s" contains a non-utf8 file content.',
            language_code,
            transcript_file_name,
            edx_video_id
        )

    def test_import_existing_video_transcript(self):
        """
        Verify that transcript import for existing video with transcript attached is working as expected.
        """
        expected_video_transcripts = [self.transcript_data3]

        import_xml = self.make_import_xml(
            video_dict=constants.VIDEO_DICT_FISH,
            video_transcripts=expected_video_transcripts
        )

        # Verify video is present before.
        video = Video.objects.get(edx_video_id=constants.VIDEO_DICT_FISH['edx_video_id'])
        self.assertIsNotNone(video)

        # Create internal video transcripts
        transcript_data = dict(constants.VIDEO_TRANSCRIPT_3PLAY, video=video)
        transcript_data = omit_attrs(transcript_data, ['video_id', 'file_data'])
        VideoTranscript.objects.create(**transcript_data)

        # Verify that video has expected transcripts before import.
        self.assert_transcripts(
            constants.VIDEO_DICT_FISH['edx_video_id'],
            expected_video_transcripts
        )

        api.import_from_xml(
            import_xml,
            constants.VIDEO_DICT_FISH['edx_video_id'],
            self.file_system,
            constants.EXPORT_IMPORT_STATIC_DIR,
            {},
            'test_course_id'
        )

        # Verify that video has expected transcripts after import.
        self.assert_transcripts(
            constants.VIDEO_DICT_FISH['edx_video_id'],
            expected_video_transcripts
        )

    def test_import_transcript_attached_existing_video(self):
        """
        Verify that transcript import for existing video with no transcript attached is working as expected.
        """
        exported_video_transcripts = [
            dict(constants.VIDEO_TRANSCRIPT_CIELO24, video_id=constants.VIDEO_DICT_FISH['edx_video_id']),
            dict(constants.VIDEO_TRANSCRIPT_3PLAY, video_id=constants.VIDEO_DICT_FISH['edx_video_id'])
        ]

        # Verify video is present before.
        video = Video.objects.get(edx_video_id=constants.VIDEO_DICT_FISH['edx_video_id'])
        self.assertIsNotNone(video)

        import_xml = self.make_import_xml(
            video_dict=constants.VIDEO_DICT_FISH,
            video_transcripts=exported_video_transcripts
        )

        # There must not be any transcript before import.
        self.assert_transcripts(constants.VIDEO_DICT_FISH['edx_video_id'], [])

        api.import_from_xml(
            import_xml,
            constants.VIDEO_DICT_FISH['edx_video_id'],
            self.file_system,
            constants.EXPORT_IMPORT_STATIC_DIR,
            {},
            'test_course_id'
        )

        # Verify that transcripts record are created correctly.
        self.assert_transcripts(
            constants.VIDEO_DICT_FISH['edx_video_id'],
            exported_video_transcripts,
        )

    def test_import_transcript_new_video(self):
        """
        Verify that transcript import for new video is working as expected when transcript is present in XML.
        """
        expected_video_transcripts = [self.transcript_data1, self.transcript_data2]

        import_xml = self.make_import_xml(
            video_dict=constants.VIDEO_DICT_STAR,
            video_transcripts=expected_video_transcripts
        )

        # Verify video is not present before.
        with self.assertRaises(Video.DoesNotExist):
            Video.objects.get(edx_video_id=constants.VIDEO_DICT_STAR['edx_video_id'])

        # There must not be any transcript before import.
        self.assert_transcripts(constants.VIDEO_DICT_STAR['edx_video_id'], [])

        api.import_from_xml(
            import_xml,
            constants.VIDEO_DICT_STAR['edx_video_id'],
            self.file_system,
            constants.EXPORT_IMPORT_STATIC_DIR,
            {},
            'test_course_id'
        )

        # Verify that transcript record is created with correct data.
        self.assert_transcripts(
            constants.VIDEO_DICT_STAR['edx_video_id'],
            expected_video_transcripts
        )

    @patch('edxval.api.logger')
    def test_video_transcript_missing_attribute(self, mock_logger):
        """
        Verify that video transcript import working as expected if transcript xml data is missing.
        """
        video_id = 'super-soaker'
        transcript_xml = u'<transcript file_format="srt" provider="Cielo24"/>'
        xml = etree.fromstring("""
            <video_asset>
                <transcripts>
                    {transcript_xml}
                    <transcript language_code="de" file_format="sjson" provider="3PlayMedia"/>
                </transcripts>
            </video_asset>
        """.format(transcript_xml=transcript_xml))

        # There should be no video transcript before import
        with self.assertRaises(VideoTranscript.DoesNotExist):
            VideoTranscript.objects.get(video__edx_video_id=video_id)

        # Create transcript files
        utils.create_file_in_fs(
            constants.TRANSCRIPT_DATA['wow'],
            u'super-soaker-de.sjson',
            self.file_system,
            constants.EXPORT_IMPORT_STATIC_DIR
        )
        api.create_transcript_objects(xml, video_id, self.file_system, constants.EXPORT_IMPORT_STATIC_DIR, {})

        mock_logger.warning.assert_called_with(
            "VAL: Required attributes are missing from xml, xml=[%s]",
            transcript_xml.encode('utf8')
        )

        self.assert_transcripts(video_id, [self.transcript_data3])


class GetCourseVideoRemoveTest(TestCase):
    """
    Tests to check `remove_video_for_course` function works correctly
    """

    def setUp(self):
        """
        Creates video objects for courses
        """
        # create video in the test course
        super(GetCourseVideoRemoveTest, self).setUp()
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
        videos, __ = api.get_videos_for_course(self.course_id)
        videos = list(videos)
        self.assertEqual(len(videos), 1)

        # remove the video and verify that video is removed from correct course
        api.remove_video_for_course(self.course_id, self.edx_video_id)
        videos, __ = api.get_videos_for_course(self.course_id)
        videos = list(videos)
        self.assertEqual(len(videos), 0)

        # verify that CourseVideo related object exists(soft removal) for removed video
        course_video = CourseVideo.objects.get(course_id=self.course_id, video__edx_video_id=self.edx_video_id)
        self.assertEqual(course_video.is_hidden, True)

        # verify that video still exists for other course
        videos, __ = api.get_videos_for_course('other-course')
        videos = list(videos)
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


class CourseVideoImageTest(TestCase):
    """
    Tests to check course video image related functions works correctly.
    """

    def setUp(self):
        """
        Creates video objects for courses.
        """
        super(CourseVideoImageTest, self).setUp()
        self.course_id = 'test-course'
        self.course_id2 = 'test-course2'
        self.video = Video.objects.create(**constants.VIDEO_DICT_FISH)
        self.edx_video_id = self.video.edx_video_id
        self.course_video = CourseVideo.objects.create(video=self.video, course_id=self.course_id)
        self.course_video2 = CourseVideo.objects.create(video=self.video, course_id=self.course_id2)
        self.image_path1 = 'edxval/tests/data/image.jpg'
        self.image_path2 = 'edxval/tests/data/edx.jpg'
        self.image_url = api.update_video_image(
            self.edx_video_id, self.course_id, ImageFile(open(self.image_path1, 'rb')), 'image.jpg'
        )
        self.image_url2 = api.update_video_image(
            self.edx_video_id, self.course_id2, ImageFile(open(self.image_path2, 'rb')), 'image.jpg'
        )

    def test_update_video_image(self):
        """
        Verify that `update_video_image` api function works as expected.
        """
        self.assertEqual(self.course_video.video_image.image.name, self.image_url)
        self.assertEqual(self.course_video2.video_image.image.name, self.image_url2)
        self.assertEqual(ImageFile(open(self.image_path1, 'rb')).size, ImageFile(open(self.image_url, 'rb')).size)
        self.assertEqual(ImageFile(open(self.image_path2, 'rb')).size, ImageFile(open(self.image_url2, 'rb')).size)

    def test_get_course_video_image_url(self):
        """
        Verify that `get_course_video_image_url` api function works as expected.
        """
        image_url = api.get_course_video_image_url(self.course_id, self.edx_video_id)
        self.assertEqual(self.image_url, image_url)

    def test_get_course_video_image_url_no_image(self):
        """
        Verify that `get_course_video_image_url` api function returns None when no image is found.
        """
        self.course_video.video_image.delete()
        image_url = api.get_course_video_image_url(self.course_id, self.edx_video_id)
        self.assertIsNone(image_url)

    def test_num_queries_update_video_image(self):
        """
        Test number of queries executed to upload a course video image.
        """
        with self.assertNumQueries(6):
            api.update_video_image(
                self.edx_video_id, self.course_id, ImageFile(open(self.image_path1, 'rb')), 'image.jpg'
            )

    def test_num_queries_get_course_video_image_url(self):
        """
        Test number of queries executed to get a course video image url.
        """
        with self.assertNumQueries(1):
            api.get_course_video_image_url(self.course_id, self.edx_video_id)

    def test_get_videos_for_course(self):
        """
        Verify that `get_videos_for_course` api function has correct course_video_image_url.
        """
        video_data_generator, __ = api.get_videos_for_course(self.course_id)
        video_data = list(video_data_generator)[0]
        self.assertEqual(video_data['courses'][0]['test-course'], self.image_url)

    def test_get_videos_for_ids(self):
        """
        Verify that `get_videos_for_ids` api function returns response with course_video_image_url set to None.
        """
        video_data_generator = api.get_videos_for_ids([self.edx_video_id])
        video_data = list(video_data_generator)[0]
        self.assertEqual(video_data['courses'][0]['test-course'], self.image_url)

    # attr_class is django magic: https://github.com/django/django/blob/master/django/db/models/fields/files.py#L214
    @patch('edxval.models.CustomizableImageField.attr_class.save', side_effect=Exception("pretend save doesn't work"))
    @patch('edxval.models.logger')
    def test_create_or_update_logging(self, mock_logger, mock_image_save):  # pylint: disable=unused-argument
        """
        Tests correct message is logged when save to storge is failed in `create_or_update`.
        """
        with self.assertRaises(Exception) as save_exception:  # pylint: disable=unused-variable
            VideoImage.create_or_update(self.course_video, 'test.jpg', open(self.image_path2, 'rb'))

        mock_logger.exception.assert_called_with(
            'VAL: Video Image save failed to storage for course_id [%s] and video_id [%s]',
            self.course_video.course_id,
            self.course_video.video.edx_video_id
        )

    def test_update_video_image_exception(self):
        """
        Tests exception message when we hit by an exception in `update_video_image`.
        """
        does_not_course_id = 'does_not_exist'

        with self.assertRaises(Exception) as get_exception:
            api.update_video_image(self.edx_video_id, does_not_course_id, open(self.image_path2, 'rb'), 'test.jpg')

        self.assertEqual(
            get_exception.exception.args[0],
            u'VAL: CourseVideo not found for edx_video_id: {0} and course_id: {1}'.format(
                self.edx_video_id,
                does_not_course_id
            )
        )

    def test_video_image_urls_field(self):
        """
        Test `VideoImage.generated_images` field works as expected.
        """
        image_urls = ['video-images/a.png', 'video-images/b.png']

        # an empty list should be returned when there is no value for urls
        self.assertEqual(self.course_video.video_image.generated_images, [])

        # set a list with data and expect the same list to be returned
        course_video = CourseVideo.objects.create(video=self.video, course_id='course101')
        video_image = VideoImage.objects.create(course_video=course_video)
        video_image.generated_images = image_urls
        video_image.save()
        self.assertEqual(video_image.generated_images, image_urls)
        self.assertEqual(course_video.video_image.generated_images, image_urls)

    def test_video_image_urls_field_validation(self):
        """
        Test `VideoImage.generated_images` field validation.
        """
        course_video = CourseVideo.objects.create(video=self.video, course_id='course101')
        video_image = VideoImage.objects.create(course_video=course_video)

        # expect a validation error if we try to set a list with more than 3 items
        with self.assertRaises(ValidationError) as set_exception:
            video_image.generated_images = ['a', 'b', 'c', 'd']
            video_image.save()

        self.assertEqual(
            set_exception.exception.message,
            u'list must not contain more than {} items.'.format(LIST_MAX_ITEMS)
        )

        # expect a validation error if we try to a list with non-string items
        with self.assertRaises(ValidationError) as set_exception:
            video_image.generated_images = ['a', 1, 2]
            video_image.save()

        self.assertEqual(set_exception.exception.message, u'list must only contain strings.')

        # expect a validation error if we try to set non list data
        for item in ('a string', 555, {'a': 1}, (1,)):
            with self.assertRaisesRegex(ValidationError, 'is not a list') as set_exception:
                video_image.generated_images = item
                video_image.save()

    def test_video_image_urls_field_to_python_exceptions(self):
        """
        Test that `VideoImage.generated_images` field raises ValidationErrors
        when bad data is somehow in the database for this field.
        """
        course_video = CourseVideo.objects.create(video=self.video, course_id='course101')
        video_image = VideoImage.objects.create(course_video=course_video)

        # Tests that a TypeError is raised and turned into a ValidationError
        # when the value is not a list (but still JSON serializable).
        # We patch ListField.get_prep_value() to just do a json dumps without
        # doing any type checking.
        video_image.generated_images = {'key': 'image.jpeg'}
        with patch('edxval.models.ListField.get_prep_value', lambda _, value: json.dumps(value)):
            video_image.save()

        with self.assertRaisesRegex(ValidationError, 'Must be a valid list of strings'):
            video_image.refresh_from_db()

        # Tests that a ValueError is raised and turned into a ValidationError
        # when the value is not JSON serializable.
        # We patch ListField.get_prep_value() to let anything
        # be saved in this field.
        video_image.generated_images = 'image.jpeg'
        with patch('edxval.models.ListField.get_prep_value', lambda _, value: value):
            video_image.save()

        with self.assertRaisesRegex(ValidationError, 'Must be a valid list of strings'):
            video_image.refresh_from_db()

    def test_video_image_deletion_single(self):
        """
        Test video image deletion works as expected when an image is used by only the video being updated.
        """
        existing_image_name = self.course_video.video_image.image.name

        # This will replace the image for self.course_video and delete the existing image
        image_url = api.update_video_image(
            self.edx_video_id, self.course_id, ImageFile(open(self.image_path2, 'rb')), 'image.jpg'
        )

        # Verify that new image is set to course_video
        course_video = CourseVideo.objects.get(video=self.video, course_id=self.course_id)
        self.assertEqual(course_video.video_image.image.name, image_url)

        # Verify that an exception is raised if we try to open a delete image file
        with self.assertRaises(IOError) as file_open_exception:
            ImageFile(open(existing_image_name, 'rb'))

        self.assertEqual(file_open_exception.exception.strerror, u'No such file or directory')

    def test_video_image_deletion_multiple(self):
        """
        Test video image deletion works as expected if an image is used by multiple course videos.
        """
        # Set and verify both course video images to have same image
        shared_image = self.course_video.video_image.image.name = self.course_video2.video_image.image.name
        self.course_video.video_image.save()
        self.assertEqual(self.course_video.video_image.image.name, self.course_video2.video_image.image.name)

        # This will replace the image for self.course_video but image will
        # not be deleted because it is also used by self.course_video2
        api.update_video_image(self.edx_video_id, self.course_id, ImageFile(open(self.image_path2, 'rb')), 'image.jpg')

        # Verify image for course_video has changed
        course_video = CourseVideo.objects.get(video=self.video, course_id=self.course_id)
        self.assertNotEqual(course_video.video_image.image.name, shared_image)

        # Verify image for self.course_video2 has not changed
        self.assertEqual(self.course_video2.video_image.image.name, shared_image)

        # Open the shared image file to verify it is not deleted
        ImageFile(open(shared_image, 'rb'))


@ddt
class TranscriptTest(TestCase):
    """
    Tests to check transcript related functions.
    """
    def setUp(self):
        """
        Creates video and video transcript objects.
        """
        super(TranscriptTest, self).setUp()
        self.flash_transcript_path = 'edxval/tests/data/The_Flash.srt'
        self.arrow_transcript_path = 'edxval/tests/data/The_Arrow.srt'

        # Set up a video (video_id -> super-soaker) with 'en' and 'fr' transcripts.
        video_and_transcripts = self.setup_video_with_transcripts(
            video_data=constants.VIDEO_DICT_FISH,
            transcripts_data=[
                {
                    'language_code': 'en',
                    'provider': TranscriptProviderType.THREE_PLAY_MEDIA,
                    'file_name': None,
                    'file_format': utils.TranscriptFormat.SRT,
                    'file_data': File(open(self.flash_transcript_path, 'rb'))
                },
                {
                    'language_code': 'fr',
                    'provider': TranscriptProviderType.CIELO24,
                    'file_name': None,
                    'file_format': utils.TranscriptFormat.SRT,
                    'file_data': ContentFile(constants.TRANSCRIPT_DATA['overwatch'])
                }
            ]
        )
        self.video1 = video_and_transcripts['video']
        self.v1_transcript1 = video_and_transcripts['transcripts']['en']
        self.v1_transcript2 = video_and_transcripts['transcripts']['fr']

        # Set up another video (video_id -> medium-soaker) with 'de' and 'zh' transcripts.
        video_and_transcripts = self.setup_video_with_transcripts(
            video_data=constants.VIDEO_DICT_DIFFERENT_ID_FISH,
            transcripts_data=[
                {
                    'language_code': 'de',
                    'provider': TranscriptProviderType.CUSTOM,
                    'file_name': None,
                    'file_format': utils.TranscriptFormat.SRT,
                    'file_data': File(open(self.arrow_transcript_path, 'rb'))
                },
                {
                    'language_code': 'zh',
                    'provider': TranscriptProviderType.CUSTOM,
                    'file_name': 'non/existent/transcript/path',
                    'file_format': utils.TranscriptFormat.SRT,
                    'file_data': None
                }
            ]
        )
        self.video2 = video_and_transcripts['video']
        self.v2_transcript1 = video_and_transcripts['transcripts']['de']
        self.v2_transcript2 = video_and_transcripts['transcripts']['zh']

        self.temp_dir = mkdtemp()
        self.addCleanup(shutil.rmtree, self.temp_dir)

    def setup_video_with_transcripts(self, video_data, transcripts_data):
        """
        Setup a video with transcripts and returns them
        """
        result = dict(video=None, transcripts={})
        result['video'] = Video.objects.create(**video_data)
        for transcript_data in transcripts_data:
            language_code = transcript_data['language_code']
            transcript, __ = VideoTranscript.create_or_update(
                video=result['video'],
                language_code=language_code,
                metadata={
                    'file_name': transcript_data['file_name'],
                    'file_format': transcript_data['file_format'],
                    'provider': transcript_data['provider']
                },
                file_data=transcript_data['file_data']
            )
            result['transcripts'][language_code] = transcript

        return result

    def tearDown(self):
        """
        Reverse the setup
        """
        # Remove the transcript files
        super(TranscriptTest, self).tearDown()
        self.v1_transcript1.transcript.delete()
        self.v1_transcript2.transcript.delete()
        self.v2_transcript1.transcript.delete()

    @data(
        {'video_id': 'super-soaker', 'language_code': 'en', 'expected_availability': True},
        {'video_id': 'super-soaker', 'language_code': None, 'expected_availability': True},
        {'video_id': 'super123', 'language_code': 'en', 'expected_availability': False},
        {'video_id': 'super-soaker', 'language_code': 'ro', 'expected_availability': False},
        {'video_id': 'medium-soaker', 'language_code': 'de', 'expected_availability': True},
    )
    @unpack
    def test_is_transcript_available(self, video_id, language_code, expected_availability):
        """
        Verify that `is_transcript_available` api function works as expected.
        """
        is_transcript_available = api.is_transcript_available(video_id, language_code)
        self.assertEqual(is_transcript_available, expected_availability)

    @data(
        {'video_id': 'non-existant-video', 'language_code': 'en'},
        {'video_id': '0987654321', 'language_code': 'en'},
    )
    @unpack
    def test_get_video_transcript_not_found(self, video_id, language_code):
        """
        Verify that `get_video_transcript` works as expected if transcript is not found.
        """
        self.assertIsNone(api.get_video_transcript(video_id, language_code))

    def test_get_video_transcript(self):
        """
        Verify that `get_video_transcript` works as expected if transcript is found.
        """
        transcript = api.get_video_transcript(u'super-soaker', u'fr')
        expectation = {
            'video_id': u'super-soaker',
            'url': self.v1_transcript2.url(),
            'file_format': utils.TranscriptFormat.SRT,
            'provider': TranscriptProviderType.CIELO24,
            'language_code': u'fr'
        }
        self.assertDictEqual(transcript, expectation)

    @patch('edxval.api.logger')
    def test_get_video_transcript_data_exception(self, mock_logger):
        """
        Verify that `get_video_transcript_data` logs and raises an exception.
        """
        video_id = u'medium-soaker'
        language_code = u'zh'
        with self.assertRaises(IOError):
            api.get_video_transcript_data(video_id, language_code)

        mock_logger.exception.assert_called_with(
            '[edx-val] Error while retrieving transcript for video=%s -- language_code=%s',
            video_id,
            language_code,
        )

    def test_get_video_transcript_data_not_found(self):
        """
        Verify the `get_video_transcript_data` returns none if transcript is not present for a video.
        """
        transcript = api.get_video_transcript_data(u'non-existant-video', u'en')
        self.assertIsNone(transcript)

    @data(
        ('super-soaker', 'en', 'Shallow Swordfish-en.srt', 'edxval/tests/data/The_Flash.srt'),
        ('medium-soaker', 'de', 'Shallow Swordfish-de.srt', 'edxval/tests/data/The_Arrow.srt')
    )
    @unpack
    def test_get_video_transcript_data(self, video_id, language_code, expected_file_name, expected_transcript_path):
        """
        Verify that `get_video_transcript_data` api function works as expected.
        """
        expected_transcript = {
            'file_name': expected_file_name,
            'content': File(open(expected_transcript_path, 'rb')).read()
        }
        transcript = api.get_video_transcript_data(video_id=video_id, language_code=language_code)
        self.assertDictEqual(transcript, expected_transcript)

    def test_get_video_transcript_url(self):
        """
        Verify that `get_video_transcript_url` api function works as expected.
        """
        transcript_url = api.get_video_transcript_url('super-soaker', 'fr')
        self.assertEqual(transcript_url, self.v1_transcript2.url())

    @data(
        {
            'file_data': None,
            'file_name': 'overwatch.sjson',
            'file_format': utils.TranscriptFormat.SJSON,
            'language_code': 'da',
            'provider': TranscriptProviderType.CIELO24
        },
        {
            'file_data': ContentFile(constants.TRANSCRIPT_DATA['overwatch']),
            'file_name': None,
            'file_format': utils.TranscriptFormat.SRT,
            'language_code': 'es',
            'provider': TranscriptProviderType.THREE_PLAY_MEDIA
        },
    )
    @unpack
    def test_create_or_update_video_transcript(self, file_data, file_name, file_format, language_code, provider):
        """
        Verify that `create_or_update_video_transcript` api function updates existing transcript as expected.
        """
        edx_video_id = 'super-soaker'
        video_transcript = VideoTranscript.objects.get(video__edx_video_id=edx_video_id, language_code='en')
        self.assertIsNotNone(video_transcript)

        transcript_url = api.create_or_update_video_transcript(
            video_id=edx_video_id,
            language_code='en',
            metadata=dict(
                provider=provider,
                language_code=language_code,
                file_name=file_name,
                file_format=file_format
            ),
            file_data=file_data
        )

        # Now, Querying Video Transcript with previous/old language code leads to DoesNotExist
        with self.assertRaises(VideoTranscript.DoesNotExist):
            VideoTranscript.objects.get(video__edx_video_id=edx_video_id, language_code='en')

        # Assert the updates to the transcript object
        video_transcript = VideoTranscript.objects.get(video__edx_video_id=edx_video_id, language_code=language_code)
        self.assertEqual(transcript_url, video_transcript.url())
        self.assertEqual(video_transcript.file_format, file_format)
        self.assertEqual(video_transcript.provider, provider)
        self.assertEqual(video_transcript.language_code, language_code)

        if file_data:
            self.assertTrue(transcript_url.startswith(settings.VIDEO_TRANSCRIPTS_SETTINGS['DIRECTORY_PREFIX']))
            self.assertEqual(video_transcript.transcript.name, transcript_url)
            with open(video_transcript.transcript.name, encoding='utf8') as saved_transcript:
                self.assertEqual(saved_transcript.read(), constants.TRANSCRIPT_DATA['overwatch'])
        else:
            self.assertEqual(video_transcript.transcript.name, file_name)

    @data(
        {
            'video_id': 'super-soaker',
            'file_format': '123',
            'provider': TranscriptProviderType.CIELO24,
            'exception': InvalidTranscriptFormat,
            'exception_message': '123 transcript format is not supported',
        },
        {
            'video_id': 'medium-soaker',
            'file_format': utils.TranscriptFormat.SRT,
            'provider': 123,
            'exception': InvalidTranscriptProvider,
            'exception_message': '123 transcript provider is not supported',
        },
    )
    @unpack
    def test_create_or_update_video_exceptions(self, video_id, file_format, provider, exception, exception_message):
        """
        Verify that `create_or_update_video_transcript` api function raise exceptions on invalid values.
        """
        with self.assertRaises(exception) as transcript_exception:
            api.create_or_update_video_transcript(video_id, 'ur', metadata={
                'provider': provider,
                'file_format': file_format
            })

        self.assertEqual(transcript_exception.exception.args[0], exception_message)

    @mock.patch.object(VideoTranscript, 'save')
    def test_create_or_update_transcript_exception_on_update(self, mock_save):
        """
        Verify `create_or_update_video_transcript` api function does not update transcript on exception
        """
        file_data = ContentFile(constants.TRANSCRIPT_DATA['overwatch'])
        language_code = 'en'
        edx_video_id = 'super-soaker'

        mock_save.side_effect = DatabaseError
        with self.assertRaises(DatabaseError):
            api.create_or_update_video_transcript(
                video_id=edx_video_id,
                language_code=language_code,
                metadata=dict(
                    provider=TranscriptProviderType.THREE_PLAY_MEDIA,
                    file_name=None,
                    file_format=utils.TranscriptFormat.SRT
                ),
                file_data=file_data
            )

        # Assert that there are no updates to the transcript data
        video_transcript = VideoTranscript.objects.get(video__edx_video_id=edx_video_id,
                                                       language_code=language_code)
        with open(video_transcript.transcript.name, 'rb') as saved_transcript:
            self.assertNotEqual(saved_transcript.read(), constants.TRANSCRIPT_DATA['overwatch'])

    @mock.patch.object(VideoTranscript, 'save')
    def test_create_or_update_transcript_exception_on_create(self, mock_save):
        """
        Verify `create_or_update_video_transcript` api function does not create transcript on exception.
        """
        file_data = ContentFile(constants.TRANSCRIPT_DATA['overwatch'])
        language_code = 'ar'
        edx_video_id = 'super-soaker'

        mock_save.side_effect = DatabaseError
        with self.assertRaises(DatabaseError):
            api.create_or_update_video_transcript(
                video_id=edx_video_id,
                language_code=language_code,
                metadata=dict(
                    provider=TranscriptProviderType.THREE_PLAY_MEDIA,
                    file_name=None,
                    file_format=utils.TranscriptFormat.SRT
                ),
                file_data=file_data
            )

        # Assert that there is no transcript record
        with self.assertRaises(VideoTranscript.DoesNotExist):
            VideoTranscript.objects.get(video__edx_video_id=edx_video_id, language_code=language_code)

    def test_create_video_transcript(self):
        """
        Verify that `create_video_transcript` api function creates transcript as expected.
        """
        edx_video_id = u'1234'
        language_code = u'en'
        transcript_props = dict(
            video_id=edx_video_id,
            language_code=language_code,
            provider=TranscriptProviderType.THREE_PLAY_MEDIA,
            file_format=utils.TranscriptFormat.SRT,
            content=ContentFile(constants.TRANSCRIPT_DATA['overwatch'])
        )

        # setup video with the `edx_video_id` above.
        self.setup_video_with_transcripts(
            video_data=dict(constants.VIDEO_DICT_DIFFERENT_ID_FISH, edx_video_id=edx_video_id),
            transcripts_data=[]
        )

        # Assert that 'en' transcript is not already present.
        video_transcript = VideoTranscript.get_or_none(edx_video_id, language_code)
        self.assertIsNone(video_transcript)

        # Create the transcript
        api.create_video_transcript(**transcript_props)

        # Assert the transcript object and its content
        video_transcript = VideoTranscript.get_or_none(edx_video_id, language_code)
        self.assertIsNotNone(video_transcript)
        self.assertEqual(video_transcript.file_format, transcript_props['file_format'])
        self.assertEqual(video_transcript.provider, transcript_props['provider'])
        with open(video_transcript.transcript.name, encoding='utf8') as created_transcript:
            self.assertEqual(created_transcript.read(), constants.TRANSCRIPT_DATA['overwatch'])

    @data(
        {
            'video_id': 'super-soaker',
            'language_code': 'en',
            'file_format': '123',
            'provider': TranscriptProviderType.CIELO24,
            'exception_msg': '"123" is not a valid choice.'
        },
        {
            'video_id': 'medium-soaker',
            'language_code': 'en',
            'file_format': utils.TranscriptFormat.SRT,
            'provider': 'unknown provider',
            'exception_msg': '"unknown provider" is not a valid choice.'
        }
    )
    @unpack
    def test_create_video_transcript_exceptions(self, video_id, language_code, file_format, provider, exception_msg):
        """
        Verify that `create_video_transcript` api function raise exceptions on invalid values.
        """
        with self.assertRaises(ValCannotCreateError) as transcript_exception:
            api.create_video_transcript(
                video_id, language_code, file_format, ContentFile(constants.TRANSCRIPT_DATA['overwatch']), provider
            )

        self.assertIn(exception_msg, str(transcript_exception.exception.args[0]))

    def test_get_available_transcript_languages(self):
        """
        Verify that `get_available_transcript_languages` works as expected.
        """
        # `super-soaker` has got 'en' and 'fr' transcripts
        transcript_languages = api.get_available_transcript_languages(video_id=u'super-soaker')
        self.assertEqual(transcript_languages, ['en', 'fr'])

    @patch('edxval.api.logger')
    def test_delete_video_transcript(self, mock_logger):
        """
        Verify that `delete_video_transcript` works as expected.
        """
        query_filter = {
            'video__edx_video_id': 'super-soaker',
            'language_code': 'fr'
        }

        self.assertEqual(VideoTranscript.objects.filter(**query_filter).count(), 1)
        # current transcript path
        transcript_path = self.v1_transcript2.transcript.name
        api.delete_video_transcript(
            video_id=query_filter['video__edx_video_id'],
            language_code=query_filter['language_code']
        )
        # assert that the transcript does not exist on the path anymore.
        self.assertFalse(os.path.exists(transcript_path))
        self.assertEqual(VideoTranscript.objects.filter(**query_filter).count(), 0)
        mock_logger.info.assert_called_with(
            'Transcript is removed for video "%s" and language code "%s"',
            query_filter['video__edx_video_id'],
            query_filter['language_code']
        )

    def test_create_transcript_file(self):
        """
        Tests that transcript file is created correctly.
        """
        language_code = 'en'
        video_id = constants.VIDEO_DICT_FISH['edx_video_id']
        transcript_file_name = u'super-soaker-en.srt'
        expected_transcript_path = combine(
            combine(self.temp_dir, constants.EXPORT_IMPORT_COURSE_DIR),
            combine(constants.EXPORT_IMPORT_STATIC_DIR, transcript_file_name)
        )

        delegate_fs = OSFS(self.temp_dir)
        file_system = delegate_fs.makedir(constants.EXPORT_IMPORT_COURSE_DIR, recreate=True)
        file_system.makedir(constants.EXPORT_IMPORT_STATIC_DIR, recreate=True)

        # Create transcript file now.
        api.create_transcript_file(
            video_id=video_id,
            language_code=language_code,
            file_format=utils.TranscriptFormat.SRT,
            static_dir=constants.EXPORT_IMPORT_STATIC_DIR,
            resource_fs=file_system
        )

        # Verify transcript file is created.
        self.assertIn(transcript_file_name, file_system.listdir(constants.EXPORT_IMPORT_STATIC_DIR))

        # Also verify the content of created transcript file.
        expected_transcript_content = File(open(expected_transcript_path, 'rb')).read()
        transcript = api.get_video_transcript_data(video_id=video_id, language_code=language_code)
        self.assertEqual(transcript['content'], expected_transcript_content)

    def test_unpublished_create_transcript_file(self):
        """
        Tests that an unpublished transcript file is created correctly.

        Scenario:
        In a course with unpublished transcript, static_dir directory isn't made
        so we don't explicitly make static_dir in this test
        exporting the transcript will make static_dir inside file_system if not present
        """
        language_code = 'en'
        video_id = constants.VIDEO_DICT_FISH['edx_video_id']
        transcript_file_name = 'super-soaker-en.srt'
        expected_transcript_path = combine(
            combine(self.temp_dir, constants.EXPORT_IMPORT_COURSE_DIR),
            combine(constants.EXPORT_IMPORT_STATIC_DIR, transcript_file_name)
        )

        delegate_fs = OSFS(self.temp_dir)
        file_system = delegate_fs.makedir(constants.EXPORT_IMPORT_COURSE_DIR, recreate=True)

        api.create_transcript_file(
            video_id=video_id,
            language_code=language_code,
            file_format=utils.TranscriptFormat.SRT,
            static_dir=constants.EXPORT_IMPORT_STATIC_DIR,
            resource_fs=file_system
        )

        self.assertIn(transcript_file_name, file_system.listdir(constants.EXPORT_IMPORT_STATIC_DIR))

        expected_transcript_content = File(open(expected_transcript_path, 'rb')).read()
        transcript = api.get_video_transcript_data(video_id=video_id, language_code=language_code)
        self.assertEqual(transcript['content'], expected_transcript_content)

    @data(
        ('invalid-video-id', 'invalid-language-code'),
        ('super-soaker', 'invalid-language-code')
    )
    @unpack
    def test_no_create_transcript_file(self, video_id, language_code):
        """
        Tests that no transcript file is created in case of invalid scenario.
        """
        file_system = OSFS(self.temp_dir)
        file_system.makedir(constants.EXPORT_IMPORT_STATIC_DIR, recreate=True)

        # Try to create transcript file now.
        api.create_transcript_file(
            video_id=video_id,
            language_code=language_code,
            file_format=utils.TranscriptFormat.SRT,
            static_dir=constants.EXPORT_IMPORT_STATIC_DIR,
            resource_fs=file_system
        )

        # Verify no file is created.
        self.assertEqual(file_system.listdir(constants.EXPORT_IMPORT_STATIC_DIR), [])


@ddt
class TranscriptPreferencesTest(TestCase):
    """
    TranscriptPreferences API Tests
    """
    def setUp(self):
        """
        Tests setup
        """
        super(TranscriptPreferencesTest, self).setUp()
        self.course_id = 'edX/DemoX/Demo_Course'
        self.transcript_preferences = TranscriptPreference.objects.create(
            **constants.TRANSCRIPT_PREFERENCES_CIELO24
        )
        self.prefs = dict(constants.TRANSCRIPT_PREFERENCES_CIELO24)
        self.prefs.update(constants.TRANSCRIPT_PREFERENCES_3PLAY)

        # casting an instance to a string returns a valid value.
        assert str(self.transcript_preferences) == 'edX/DemoX/Demo_Course - Cielo24'

    def assert_prefs(self, received, expected):
        """
        Compare `received` with `expected` and assert if not equal
        """
        # no need to compare modified datetime
        del received['modified']
        self.assertEqual(received, expected)

    def test_get_3rd_party_transcription_plans(self):
        """
        Verify that `get_3rd_party_transcription_plans` api function works as expected
        """
        self.assertEqual(
            api.get_3rd_party_transcription_plans(),
            utils.THIRD_PARTY_TRANSCRIPTION_PLANS
        )

    def test_get_transcript_preferences(self):
        """
        Verify that `get_transcript_preferences` api function works as expected
        """
        cielo24_prefs = dict(constants.TRANSCRIPT_PREFERENCES_CIELO24)
        cielo24_prefs['three_play_turnaround'] = None

        transcript_preferences = api.get_transcript_preferences(self.course_id)
        self.assert_prefs(transcript_preferences, cielo24_prefs)

    def test_remove_transcript_preferences(self):
        """
        Verify that `remove_transcript_preferences` api method works as expected.
        """
        # Verify that transcript preferences exist.
        transcript_preferences = api.get_transcript_preferences(self.course_id)
        self.assertIsNotNone(transcript_preferences)

        # Remove course wide transcript preferences.
        api.remove_transcript_preferences(self.course_id)

        # Verify now transcript preferences no longer exist.
        transcript_preferences = api.get_transcript_preferences(self.course_id)
        self.assertIsNone(transcript_preferences)

    def test_remove_transcript_preferences_not_found(self):
        """
        Verify that `remove_transcript_preferences` api method works as expected when no record is found.
        """
        course_id = 'dummy-course-id'

        # Verify that transcript preferences do not exist.
        transcript_preferences = api.get_transcript_preferences(course_id)
        self.assertIsNone(transcript_preferences)

        # Verify that calling `remove_transcript_preferences` does not break the code.
        api.remove_transcript_preferences(course_id)

    def test_update_transcript_preferences(self):
        """
        Verify that `create_or_update_transcript_preferences` api function updates as expected
        """
        transcript_preferences = api.create_or_update_transcript_preferences(**constants.TRANSCRIPT_PREFERENCES_3PLAY)
        self.assert_prefs(transcript_preferences, self.prefs)

    def test_create_transcript_preferences(self):
        """
        Verify that `create_or_update_transcript_preferences` api function creates as expected
        """
        self.prefs['course_id'] = 'edX/DemoX/Astonomy'

        # Verify that no preference is present for course id `edX/DemoX/Astonomy`
        self.assertIsNone(api.get_transcript_preferences(self.prefs['course_id']))

        # create new preference
        transcript_preferences = api.create_or_update_transcript_preferences(**self.prefs)
        self.assert_prefs(transcript_preferences, self.prefs)

        # Verify that there should be 2 preferences exists
        self.assertEqual(TranscriptPreference.objects.count(), 2)


@ddt
class TranscripCredentialsStateTest(TestCase):
    """
    ThirdPartyTranscriptCredentialsState Tests
    """
    def setUp(self):
        """
        Tests setup
        """
        super(TranscripCredentialsStateTest, self).setUp()
        third_party_trans_true = ThirdPartyTranscriptCredentialsState.objects.create(
            org='edX', provider='Cielo24', has_creds=True
        )
        third_party_trans_false = ThirdPartyTranscriptCredentialsState.objects.create(
            org='edX', provider='3PlayMedia', has_creds=False
        )

        # casting an instance to a string returns a valid value.
        assert str(third_party_trans_true) == 'edX has Cielo24 credentials'
        assert str(third_party_trans_false) == "edX doesn't have 3PlayMedia credentials"

    @data(
        {'org': 'MAX', 'provider': 'Cielo24', 'exists': True},
        {'org': 'MAX', 'provider': '3PlayMedia', 'exists': True},
        {'org': 'edx', 'provider': '3PlayMedia', 'exists': True},
    )
    @unpack
    def test_credentials_state_update(self, **kwargs):
        """
        Verify that `update_transcript_credentials_state_for_org` method works as expected
        """
        api.update_transcript_credentials_state_for_org(**kwargs)

        credentials_state = ThirdPartyTranscriptCredentialsState.objects.get(org=kwargs['org'])
        for key in kwargs:
            # The API continues to use 'exists' but the database uses 'has_creds' because
            # 'exists' is a SQL keyword.
            credentials_state_key = 'has_creds' if key == 'exists' else key
            self.assertEqual(getattr(credentials_state, credentials_state_key), kwargs[key])

    @data(
        {
            'org': 'edX',
            'provider': 'Cielo24',
            'result': {u'Cielo24': True}
        },
        {
            'org': 'edX',
            'provider': '3PlayMedia',
            'result': {u'3PlayMedia': False}
        },
        {
            'org': 'edX',
            'provider': None,
            'result': {u'3PlayMedia': False, u'Cielo24': True}
        },
        {
            'org': 'does_not_exist',
            'provider': 'does_not_exist',
            'result': {}
        },
    )
    @unpack
    def test_get_credentials_state(self, org, provider, result):
        """
        Verify that `get_transcript_credentials_state_for_org` method works as expected
        """
        credentials_state = api.get_transcript_credentials_state_for_org(org=org, provider=provider)
        self.assertEqual(credentials_state, result)
