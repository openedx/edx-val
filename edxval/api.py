# pylint: disable=E1101
# -*- coding: utf-8 -*-
"""
The internal API for VAL
"""
import logging

from edxval.models import Video
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
        new_object.id (int): id of the newly created object

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
        result (dict): Deserialized Video Object with related field EncodedVideo
            Returns all the Video object fields, and it's related EncodedVideo
            objects in a list.
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
            'url' : '/edxval/video/example',
            'edx_video_id': u'example',
            'duration': 111.0,
            'client_video_id': u'The example video',
            'encoded_videos': [
                {
                    'url': u'http://www.meowmix.com',
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

def get_videos_for_course(course_id):
    """
    Returns an iterator of videos for the given course id
    """
    videos = Video.objects.filter(courses__course_id=course_id)
    return (VideoSerializer(video).data for video in videos)
