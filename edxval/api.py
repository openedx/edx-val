# -*- coding: utf-8 -*-
"""
The internal API for VAL
"""
import logging

from edxval.models import Video
from edxval.serializers import EncodedVideoSetSerializer

logger = logging.getLogger(__name__)


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


def get_video_info(edx_video_id, location=None):
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
                edx_video_id: ID of the video
                duration: Length of video in seconds
                client_video_id: human readable ID
                encoded_video: a list of EncodedVideo dicts
                    url: url of the video
                    file_size: size of the video in bytes
                    profile: a dict of encoding details
                        profile_name: ID of the profile
                        extension: 3 letter extension of video
                        width: horizontal pixel resolution
                        height: vertical pixel resolution
            }

    Raises:
        ValVideoNotFoundError: Raised if video doesn't exist
        ValInternalError: Raised for unknown errors

    Example:
        Given one EncodedVideo with edx_video_id "thisis12char-thisis7"
        >>>
        >>> get_video_info("thisis12char-thisis7",location)
        Returns (dict):
        >>>{
        >>>    'edx_video_id': u'thisis12char-thisis7',
        >>>    'duration': 111.0,
        >>>    'client_video_id': u'Thunder Cats S01E01',
        >>>    'encoded_video': [
        >>>    {
        >>>        'url': u'http://www.meowmix.com',
        >>>        'file_size': 25556,
        >>>        'bitrate': 9600,
        >>>        'profile': {
        >>>            'profile_name': u'mobile',
        >>>            'extension': u'avi',
        >>>            'width': 100,
        >>>            'height': 101
        >>>        }
        >>>     },
        >>>    ]
        >>>}
    """
    try:
        v = Video.objects.get(edx_video_id=edx_video_id)
        result = EncodedVideoSetSerializer(v)
    except Video.DoesNotExist:
        error_message = u"Video not found for edx_video_id: {0}".format(edx_video_id)
        raise ValVideoNotFoundError(error_message)
    except Exception:
        error_message = u"Could not get edx_video_id: {0}".format(edx_video_id)
        logger.exception(error_message)
        raise ValInternalError(error_message)
    return result.data
