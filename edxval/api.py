# pylint: disable=E1101
# -*- coding: utf-8 -*-
"""
The internal API for VAL.
"""
import logging

from lxml.etree import Element, SubElement
from enum import Enum

from django.core.exceptions import ValidationError, ObjectDoesNotExist
from django.core.files.base import ContentFile

from edxval.models import Video, EncodedVideo, CourseVideo, Profile, VideoImage
from edxval.serializers import VideoSerializer
from edxval.exceptions import (  # pylint: disable=unused-import
    ValError,
    ValInternalError,
    ValVideoNotFoundError,
    ValCannotCreateError,
    ValCannotUpdateError
)

logger = logging.getLogger(__name__)  # pylint: disable=C0103


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
        video_data (dict):
         {
                url: api url to the video
                edx_video_id: ID of the video
                duration: Length of video in seconds
                client_video_id: client ID of video
                encoded_video: a list of EncodedVideo dicts
                    url: url of the video
                    file_size: size of the video in bytes
                    profile: ID of the profile
                courses: Courses associated with this video
                image: poster image file name for a particular course
         }

    Raises:
        Raises ValCannotCreateError if the video cannot be created.

    Returns the successfully created Video object
    """

    serializer = VideoSerializer(data=video_data)
    if serializer.is_valid():
        serializer.save()
        return video_data.get("edx_video_id")
    else:
        raise ValCannotCreateError(serializer.errors)


def update_video(video_data):
    """
    Called on to update Video objects in the database

    update_video is used to update Video objects by the given edx_video_id in the video_data.

    Args:
        video_data (dict):
         {
                url: api url to the video
                edx_video_id: ID of the video
                duration: Length of video in seconds
                client_video_id: client ID of video
                encoded_video: a list of EncodedVideo dicts
                    url: url of the video
                    file_size: size of the video in bytes
                    profile: ID of the profile
                courses: Courses associated with this video
         }

    Raises:
        Raises ValVideoNotFoundError if the video cannot be retrieved.
        Raises ValCannotUpdateError if the video cannot be updated.

    Returns the successfully updated Video object
    """

    try:
        video = _get_video(video_data.get("edx_video_id"))
    except Video.DoesNotExist:
        error_message = u"Video not found when trying to update video with edx_video_id: {0}".format(video_data.get("edx_video_id"))
        raise ValVideoNotFoundError(error_message)

    serializer = VideoSerializer(video, data=video_data)
    if serializer.is_valid():
        serializer.save()
        return video_data.get("edx_video_id")
    else:
        raise ValCannotUpdateError(serializer.errors)


def update_video_status(edx_video_id, status):
    """
    Update status for an existing video.

    Args:
        edx_video_id: ID of the video
        status: video status

    Raises:
        Raises ValVideoNotFoundError if the video cannot be retrieved.
    """

    try:
        video = _get_video(edx_video_id)
    except Video.DoesNotExist:
        error_message = u"Video not found when trying to update video status with edx_video_id: {0}".format(
            edx_video_id
        )
        raise ValVideoNotFoundError(error_message)

    video.status = status
    video.save()


def get_course_video_image_url(course_id, edx_video_id):
    """
    Returns course video image url or None if no image found
    """
    try:
        video_image = CourseVideo.objects.select_related('video_image').get(
            course_id=course_id, video__edx_video_id=edx_video_id
        ).video_image
        return video_image.image_url()
    except ObjectDoesNotExist:
        return None


def update_video_image(edx_video_id, course_id, image_data, file_name):
    """
    Update video image for an existing video.

    NOTE: If `image_data` is None then `file_name` value will be used as it is, otherwise
    a new file name is constructed based on uuid and extension from `file_name` value.
    `image_data` will be None in case of course re-run and export.

    Arguments:
        image_data (InMemoryUploadedFile): Image data to be saved for a course video.

    Returns:
        course video image url

    Raises:
        Raises ValVideoNotFoundError if the CourseVideo cannot be retrieved.
    """
    try:
        course_video = CourseVideo.objects.select_related('video').get(
            course_id=course_id, video__edx_video_id=edx_video_id
        )
    except ObjectDoesNotExist:
        error_message = u'VAL: CourseVideo not found for edx_video_id: {0} and course_id: {1}'.format(
            edx_video_id,
            course_id
        )
        raise ValVideoNotFoundError(error_message)

    video_image, _ = VideoImage.create_or_update(course_video, file_name, image_data)
    return video_image.image_url()


def create_profile(profile_name):
    """
    Used to create Profile objects in the database

    A profile needs to exists before an EncodedVideo object can be created.

    Args:
        profile_name (str): ID of the profile

    Raises:
        ValCannotCreateError: Raised if the profile name is invalid or exists
    """
    try:
        profile = Profile(profile_name=profile_name)
        profile.full_clean()
        profile.save()
    except ValidationError as err:
        raise ValCannotCreateError(err.message_dict)


def _get_video(edx_video_id):
    """
    Get a Video instance, prefetching encoded video and course information.

    Raises ValVideoNotFoundError if the video cannot be retrieved.
    """
    try:
        return Video.objects.prefetch_related("encoded_videos", "courses").get(edx_video_id=edx_video_id)
    except Video.DoesNotExist:
        error_message = u"Video not found for edx_video_id: {0}".format(edx_video_id)
        raise ValVideoNotFoundError(error_message)
    except Exception:
        error_message = u"Could not get edx_video_id: {0}".format(edx_video_id)
        logger.exception(error_message)
        raise ValInternalError(error_message)


def get_video_info(edx_video_id):
    """
    Retrieves all encoded videos of a video found with given video edx_video_id

    Args:
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
                    profile: ID of the profile
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
    return VideoSerializer(_get_video(edx_video_id)).data


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


def _get_videos_for_filter(video_filter, sort_field=None, sort_dir=SortDirection.asc):
    """
    Returns a generator expression that contains the videos found, sorted by
    the given field and direction, with ties broken by edx_video_id to ensure a
    total order.
    """
    videos = Video.objects.filter(**video_filter)
    if sort_field:
        # Refining by edx_video_id ensures a total order
        videos = videos.order_by(sort_field.value, "edx_video_id")
        if sort_dir == SortDirection.desc:
            videos = videos.reverse()
    return (VideoSerializer(video).data for video in videos)


def get_videos_for_course(course_id, sort_field=None, sort_dir=SortDirection.asc):
    """
    Returns an iterator of videos for the given course id.

    Args:
        course_id (String)
        sort_field (VideoSortField)
        sort_dir (SortDirection)

    Returns:
        A generator expression that contains the videos found, sorted by the
        given field and direction, with ties broken by edx_video_id to ensure a
        total order.
    """
    return _get_videos_for_filter(
        {'courses__course_id': unicode(course_id), 'courses__is_hidden': False},
        sort_field,
        sort_dir,
    )


def remove_video_for_course(course_id, edx_video_id):
    """
    Soft deletes video for particular course.

    Arguments:
        course_id (str): id of the course
        edx_video_id (str): id of the video to be hidden
    """
    course_video = CourseVideo.objects.get(course_id=course_id, video__edx_video_id=edx_video_id)
    course_video.is_hidden = True
    course_video.save()


def get_videos_for_ids(
        edx_video_ids,
        sort_field=None,
        sort_dir=SortDirection.asc
):
    """
    Returns an iterator of videos that match the given list of ids.

    Args:
        edx_video_ids (list)
        sort_field (VideoSortField)
        sort_dir (SortDirection)

    Returns:
        A generator expression that contains the videos found, sorted by the
        given field and direction, with ties broken by edx_video_id to ensure a
        total order
    """
    return _get_videos_for_filter(
        {"edx_video_id__in":edx_video_ids},
        sort_field,
        sort_dir,
    )


def get_video_info_for_course_and_profiles(course_id, profiles):
    """
    Returns a dict of edx_video_ids with a dict of requested profiles.

    Args:
        course_id (str): id of the course
        profiles (list): list of profile_names
    Returns:
        (dict): Returns all the profiles attached to a specific
        edx_video_id
        {
            edx_video_id: {
                'duration': length of the video in seconds,
                'profiles': {
                    profile_name: {
                        'url': url of the encoding
                        'file_size': size of the file in bytes
                    },
                }
            },
        }
    Example:
        Given two videos with two profiles each in course_id 'test_course':
        {
            u'edx_video_id_1': {
                u'duration: 1111,
                u'profiles': {
                    u'mobile': {
                        'url': u'http: //www.example.com/meow',
                        'file_size': 2222
                    },
                    u'desktop': {
                        'url': u'http: //www.example.com/woof',
                        'file_size': 4444
                    }
                }
            },
            u'edx_video_id_2': {
                u'duration: 2222,
                u'profiles': {
                    u'mobile': {
                        'url': u'http: //www.example.com/roar',
                        'file_size': 6666
                    },
                    u'desktop': {
                        'url': u'http: //www.example.com/bzzz',
                        'file_size': 8888
                    }
                }
            }
        }
    """
    # In case someone passes in a key (VAL doesn't really understand opaque keys)
    course_id = unicode(course_id)
    try:
        encoded_videos = EncodedVideo.objects.filter(
            profile__profile_name__in=profiles,
            video__courses__course_id=course_id
        ).select_related()
    except Exception:
        error_message = u"Could not get encoded videos for course: {0}".format(course_id)
        logger.exception(error_message)
        raise ValInternalError(error_message)

    # DRF serializers were causing extra queries for some reason...
    return_dict = {}
    for enc_vid in encoded_videos:
        # Add duration to edx_video_id
        return_dict.setdefault(enc_vid.video.edx_video_id, {}).update(
            {
                "duration": enc_vid.video.duration,
            }
        )
        # Add profile information to edx_video_id's profiles
        return_dict[enc_vid.video.edx_video_id].setdefault("profiles", {}).update(
            {enc_vid.profile.profile_name: {
                "url": enc_vid.url,
                "file_size": enc_vid.file_size,
            }}
        )
    return return_dict


def copy_course_videos(source_course_id, destination_course_id):
    """
    Adds the destination_course_id to the videos taken from the source_course_id

    Args:
        source_course_id: The original course_id
        destination_course_id: The new course_id where the videos will be copied
    """
    if source_course_id == destination_course_id:
        return

    course_videos = CourseVideo.objects.select_related('video', 'video_image').filter(
        course_id=unicode(source_course_id)
    )

    for course_video in course_videos:
        destination_course_video, __ = CourseVideo.objects.get_or_create(
            video=course_video.video,
            course_id=destination_course_id
        )
        if hasattr(course_video, 'video_image'):
            VideoImage.create_or_update(
                course_video=destination_course_video,
                file_name=course_video.video_image.image.name
            )


def export_to_xml(edx_video_id, course_id=None):
    """
    Exports data about the given edx_video_id into the given xml object.

    Args:
        edx_video_id (str): The ID of the video to export
        course_id (str): The ID of the course with which this video is associated

    Returns:
        An lxml video_asset element containing export data

    Raises:
        ValVideoNotFoundError: if the video does not exist
    """
    video_image_name = ''
    video = _get_video(edx_video_id)

    try:
        course_video = CourseVideo.objects.select_related('video_image').get(course_id=course_id, video=video)
        video_image_name = course_video.video_image.image.name
    except ObjectDoesNotExist:
        pass

    video_el = Element(
        'video_asset',
        attrib={
            'client_video_id': video.client_video_id,
            'duration': unicode(video.duration),
            'image': video_image_name
        }
    )
    for encoded_video in video.encoded_videos.all():
        SubElement(
            video_el,
            'encoded_video',
            {
                name: unicode(getattr(encoded_video, name))
                for name in ['profile', 'url', 'file_size', 'bitrate']
            }
        )
    # Note: we are *not* exporting Subtitle data since it is not currently updated by VEDA or used
    # by LMS/Studio.
    return video_el


def import_from_xml(xml, edx_video_id, course_id=None):
    """
    Imports data from a video_asset element about the given edx_video_id.

    If the edx_video_id already exists, then no changes are made. If an unknown
    profile is referenced by an encoded video, that encoding will be ignored.

    Args:
        xml: An lxml video_asset element containing import data
        edx_video_id (str): The ID for the video content
        course_id (str): The ID of a course to associate the video with
            (optional)

    Raises:
        ValCannotCreateError: if there is an error importing the video
    """
    if xml.tag != 'video_asset':
        raise ValCannotCreateError('Invalid XML')

    # If video with edx_video_id already exists, associate it with the given course_id.
    try:
        video = Video.objects.get(edx_video_id=edx_video_id)
        logger.info(
            "edx_video_id '%s' present in course '%s' not imported because it exists in VAL.",
            edx_video_id,
            course_id,
        )
        if course_id:
            course_video, __ = CourseVideo.get_or_create_with_validation(video=video, course_id=course_id)

            image_file_name = xml.get('image', '').strip()
            if image_file_name:
                VideoImage.create_or_update(course_video, image_file_name)

        return
    except ValidationError as err:
        logger.exception(err.message)
        raise ValCannotCreateError(err.message_dict)
    except Video.DoesNotExist:
        pass

    # Video with edx_video_id did not exist, so create one from xml data.
    data = {
        'edx_video_id': edx_video_id,
        'client_video_id': xml.get('client_video_id'),
        'duration': xml.get('duration'),
        'status': 'imported',
        'encoded_videos': [],
        'courses': [{course_id: xml.get('image')}] if course_id else [],
    }
    for encoded_video_el in xml.iterfind('encoded_video'):
        profile_name = encoded_video_el.get('profile')
        try:
            Profile.objects.get(profile_name=profile_name)
        except Profile.DoesNotExist:
            logger.info(
                "Imported edx_video_id '%s' contains unknown profile '%s'.",
                edx_video_id,
                profile_name
            )
            continue
        data['encoded_videos'].append({
            'profile': profile_name,
            'url': encoded_video_el.get('url'),
            'file_size': encoded_video_el.get('file_size'),
            'bitrate': encoded_video_el.get('bitrate'),
        })
    create_video(data)
