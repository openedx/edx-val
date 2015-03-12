# pylint: disable=E1101
# -*- coding: utf-8 -*-
"""
The internal API for VAL. This is not yet stable
"""
from enum import Enum
import logging

from edxval.models import Video, EncodedVideo, CourseVideo
from edxval.serializers import VideoSerializer, ProfileSerializer

logger = logging.getLogger(__name__)  # pylint: disable=C0103


class ValError(Exception):
    """
    An error that occurs during VAL actions.

    This error is raised when the VAL API cannot perform a requested
    action.

    """
    pass


class ValInternalError(ValError):
    """
    An error internal to the VAL API has occurred.

    This error is raised when an error occurs that is not caused by incorrect
    use of the API, but rather internal implementation of the underlying
    services.

    """
    pass


class ValVideoNotFoundError(ValError):
    """
    This error is raised when a video is not found

    If a state is specified in a call to the API that results in no matching
    entry in database, this error may be raised.

    """
    pass


class ValCannotCreateError(ValError):
    """
    This error is raised when an object cannot be created
    """
    pass


class VideoSortField(Enum):
    """An enum representing sortable fields in the Video model"""
    created = "created"
    edx_video_id = "edx_video_id"
    client_video_id = "client_video_id"
    duration = "duration"
    # status omitted because user-facing strings do not match data


class SortDirection(Enum):
    """An enum representing sort direction"""
    asc = "asc"
    desc = "desc"


def create_video(video_data):
    """
    Called on to create Video objects in the database

    create_video is used to create Video objects whose children are EncodedVideo
    objects which are linked to Profile objects. This is an alternative to the HTTP
    requests so it can be used internally. The VideoSerializer is used to
    deserialize this object. If there are duplicate profile_names, the entire
    creation will be rejected. If the profile is not found in the database, the
    video will not be created.
    Args:
        data (dict):
         {
                url: api url to the video
                edx_video_id: ID of the video
                duration: Length of video in seconds
                client_video_id: client ID of video
                encoded_video: a list of EncodedVideo dicts
                    url: url of the video
                    file_size: size of the video in bytes
                    profile: a dict of encoding details
                        profile_name: ID of the profile
                        extension: 3 letter extension of video
                        width: horizontal pixel resolution
                        height: vertical pixel resolution
                courses: Courses associated with this video
         }
    """
    serializer = VideoSerializer(data=video_data)
    if serializer.is_valid():
        serializer.save()
        return video_data.get("edx_video_id")
    else:
        raise ValCannotCreateError(serializer.errors)


def create_profile(profile_data):
    """
    Used to create Profile objects in the database

    A profile needs to exists before an EncodedVideo object can be created.

    Args:
        data (dict):
        {
            profile_name: ID of the profile
            extension: 3 letter extension of video
            width: horizontal pixel resolution
            height: vertical pixel resolution
        }

    Returns:
        (int): id of the newly created object

    Raises:
        ValCannotCreateError: Raised if the serializer throws an error
    """
    serializer = ProfileSerializer(data=profile_data)
    if serializer.is_valid():
        serializer.save()
        return profile_data.get("profile_name")
    else:
        raise ValCannotCreateError(serializer.errors)


def get_video_info(edx_video_id, location=None):  # pylint: disable=W0613
    """
    Retrieves all encoded videos of a video found with given video edx_video_id

    Args:
        location (str): geographic locations used determine CDN
        edx_video_id (str): id for video content.

    Returns:
        (dict): Deserialized Video Object with related field EncodedVideo
            Returns all the Video object fields, and it's related EncodedVideo
            objects in a list.
            {
                url: api url to the video
                edx_video_id: ID of the video
                status: Status of the video as a string
                duration: Length of video in seconds
                client_video_id: client ID of video
                encoded_video: a list of EncodedVideo dicts
                    url: url of the video
                    file_size: size of the video in bytes
                    profile: a dict of encoding details
                        profile_name: ID of the profile
                        extension: 3 letter extension of video
                        width: horizontal pixel resolution
                        height: vertical pixel resolution
                subtitles: a list of Subtitle dicts
                    fmt: file format (SRT or SJSON)
                    language: language code
                    content_url: url of file
                    url: api url to subtitle
            }

    Raises:
        ValVideoNotFoundError: Raised if video doesn't exist
        ValInternalError: Raised for unknown errors

    Example:
        Given one EncodedVideo with edx_video_id "example"
        >>> get_video_info("example")
        Returns (dict):
        {
            'url' : '/edxval/videos/example',
            'edx_video_id': u'example',
            'duration': 111.0,
            'client_video_id': u'The example video',
            'encoded_videos': [
                {
                    'url': u'http://www.example.com',
                    'file_size': 25556,
                    'bitrate': 9600,
                    'profile': u'mobile'
                 }
            ]
        }
    """
    try:
        video = Video.objects.prefetch_related("encoded_videos", "courses").get(edx_video_id=edx_video_id)
        result = VideoSerializer(video)
    except Video.DoesNotExist:
        error_message = u"Video not found for edx_video_id: {0}".format(edx_video_id)
        raise ValVideoNotFoundError(error_message)
    except Exception:
        error_message = u"Could not get edx_video_id: {0}".format(edx_video_id)
        logger.exception(error_message)
        raise ValInternalError(error_message)
    return result.data  # pylint: disable=E1101


def get_urls_for_profiles(edx_video_id, profiles):
    """
    Returns a dict mapping profiles to URLs.

    If the profiles or video is not found, urls will be blank.

    Args:
        edx_video_id (str): id of the video
        profiles (list): list of profiles we want to search for

    Returns:
        (dict): A dict containing the profile to url pair
    """
    profiles_to_urls = {profile: None for profile in profiles}
    try:
        video_info = get_video_info(edx_video_id)
    except ValVideoNotFoundError:
        return profiles_to_urls

    for encoded_video in video_info["encoded_videos"]:
        if encoded_video["profile"] in profiles:
            profiles_to_urls[encoded_video["profile"]] = encoded_video["url"]

    return profiles_to_urls


def get_url_for_profile(edx_video_id, profile):
    """
    Uses get_urls_for_profile to obtain a single profile

    Args:
        edx_video_id (str): id of the video
        profile (str): a string of the profile we are searching

    Returns:
        (str): A string with the url

    """
    return get_urls_for_profiles(edx_video_id, [profile])[profile]


def get_videos_for_course(course_id):
    """
    Returns an iterator of videos for the given course id
    """
    videos = Video.objects.filter(courses__course_id=unicode(course_id))
    return (VideoSerializer(video).data for video in videos)


def get_videos_for_ids(
        edx_video_ids,
        sort_field=None,
        sort_dir=SortDirection.asc
):
    """
    Returns an iterator of videos that match the given list of ids

    Args:
        edx_video_ids (list)
        sort_field (VideoSortField)
        sort_dir (SortDirection)

    Returns:
        A generator expression that contains the videos found, sorted by the
        given field and direction, with ties broken by edx_video_id to ensure a
        total order
    """
    videos = Video.objects.filter(edx_video_id__in=edx_video_ids)
    if sort_field:
        # Refining by edx_video_id ensures a total order
        videos = videos.order_by(sort_field.value, "edx_video_id")
        if sort_dir == SortDirection.desc:
            videos = videos.reverse()
    return (VideoSerializer(video).data for video in videos)


def get_video_info_for_course_and_profile(course_id, profile_name):
    """
    Returns a dict of edx_video_ids with a dict of requested profiles.

    If the profiles or video is not found, urls will be blank.

    Args:
        course_id (str): id of the course
        profiles (list): list of profile_names
    Returns:
        (dict): Returns all the profiles attached to a specific
        edx_video_id
        {
            edx_video_id: {
                profile_name: {
                    'url': url of the encoding
                    'duration': length of the video in seconds
                    'file_size': size of the file in bytes
                },
            },
        }
    Example:
        Given two videos with two profiles each in course_id 'test_course':
        {
            u'edx_video_id_1': {
                u'mobile': {
                    'url': u'http: //www.example.com/meow',
                    'duration': 1111,
                    'file_size': 2222
                },
                u'desktop': {
                    'url': u'http: //www.example.com/woof',
                    'duration': 3333,
                    'file_size': 4444
                }
            },
            u'edx_video_id_2': {
                u'mobile': {
                    'url': u'http: //www.example.com/roar',
                    'duration': 5555,
                    'file_size': 6666
                },
                u'desktop': {
                    'url': u'http: //www.example.com/bzzz',
                    'duration': 7777,
                    'file_size': 8888
                }
            }
        }
    """
    #TODO This function needs unit tests. Write them when addressing MA-169
    # In case someone passes in a key (VAL doesn't really understand opaque keys)
    course_id = unicode(course_id)
    try:
        encoded_videos = EncodedVideo.objects.filter(
            profile__profile_name=profile_name,
            video__courses__course_id=course_id
        ).select_related()
    except Exception:
        error_message = u"Could not get encoded videos for course: {0}".format(course_id)
        logger.exception(error_message)
        raise ValInternalError(error_message)

    # DRF serializers were causing extra queries for some reason...
    return {
        enc_vid.video.edx_video_id: {
            "url": enc_vid.url,
            "file_size": enc_vid.file_size,
            "duration": enc_vid.video.duration,
        }
        for enc_vid in encoded_videos
    }


def copy_course_videos(old_course_id, new_course_id):
    """
    Adds the new_course_id to the videos taken from the old_course_id

    Args:
        old_course_id: The original course_id
        new_course_id: The new course_id of the rerun
    """
    if old_course_id == new_course_id:
        raise ValueError(
            "Both course_id's are the same: {}".format(new_course_id)
        )
    if Video.objects.filter(courses__course_id=unicode(new_course_id)):
        raise ValCannotCreateError(
            "New course id already exists: {}".format(new_course_id)
        )
    videos = Video.objects.filter(courses__course_id=unicode(old_course_id))

    for video in videos:
        CourseVideo.objects.create(
            video=video,
            course_id=new_course_id
        )
