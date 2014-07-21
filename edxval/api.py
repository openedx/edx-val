"""
The internal API for VAL
"""

from edxval.models import Video, Profile, EncodedVideo
from edxval.serializers import (
    deserialize_video_upload
)

from django.db import DatabaseError
from django.core.exceptions import ObjectDoesNotExist


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
    This error is raised when a request is not found

    If a state is specified in a call to the API that results in no matching
    entry in database, this error may be raised.

    """
    pass


class ValNotAvailableError(ValError):
    """
    This error is raised when no video of the requested format is found.

    If a state is specified in a call to the API that results in no matching
    video format, this error may be raised.

    """
    pass


class ValRequestError(ValError):
    """
    This error is raised when there was a request-specific error

    This error is reserved for problems specific to the use of the API.

    """
    pass


class ValInvalidParametersError(ValError):
    """
    This error is raised when parameters are invalid
    """


def update_create_encoded_video(video_dict, encoded_dict, profile_info):
    """
    Updates or creates an EncodedVideo that with the given arguments.

    Attempts to update the specified EncodedVideo. If it does not exist,
    the video_dict, if valid, will be used to create a new EncodedVideo.

    Args:
        video (dict):
        encoded_video (dict):
        profile (dict):

    Returns:
        >>> commit on success, look up later

    Raises:
        >>> fill this later

    Examples:
        >>> encoded_dict = dict(
        >>>    edx_video_id="thisis12char-thisis7_mob",
        >>>    url="www.meowmix.com",
        >>>    file_size=25556,
        >>>    duration=300,
        >>>    bitrate=9600,
        >>> )
        >>> video_dict=dict(
        >>>         client_title="Thunder Cats",
        >>>         edx_video_prefix="thisis12char-thisis7_mob",
        >>>         duration=1234,
        >>> )
        >>> profile_info = "mobile"
        >>> update_or_create_encoded_video(video_dict, encoded_dict, profile)

    """

    try:
        return deserialize_video_upload(video_dict, encoded_dict, profile_info)
    except ValInternalError:
        error_message = "Unknown internal error when creating EncodedVideo"
        raise ValInternalError(error_message)


def get_video_info(edx_video_query, location=None):
    """
    Retrieves video content information based on given video content

    Args:
        location (str): geographic locations used determine CDN
        edx_v_id_pre (str): id for video content. It is a 20 character
            string where the first 20 identifies the course and video.

    Returns:
        result (dict): a dict with the a dict of urls for all video formats
            and key/value pairs of other information such as duration or
            resolution.

    Raises:
        ValRequestError: Raised if search parameters are not valid
        ValVideoNotFoundError: Raised if video doesn't exist
        ValInternalError: Raised for unknown errors

    Example:
        >>> get_video_info("HARSPU27T313-V025000",location)
        {
            'url':{
                'mhq':'www.thevideo.com/thevideo/mobilehighquality'
                'mlq':'www.thevideo.com/thevideo/mobilelowquality'
                'dhq':'www.thevideo.com/thevideo/desktophighquality'
                'dlq':'www.thevideo.com/thevideo/desktophighquality'
                }
            'duration':10000
            'title':'Wizards of the Cheese'
        }

    """
    raise NotImplementedError


def get_duration(course_id, section=None, subsection=None):
    """
    Retrieves total time of all videos with given parameters

    Takes the given parameters and adds up the durations of all the videos.

    Args:
        course_id (str): The id of the course
        section (str): The section
        subsection (str): The subsection of section

    Returns:
        int: Duration of all videos in seconds

    Raises:
        ValRequestError: Raised if parameters are not valid
        ValVideoNotFound: Raised if a parameter is not found
        ValInternalError: Raised for unknown errors
    """
    raise NotImplementedError


def _check_edx_video_id(the_id):
    """
    Checks if the edx_video_id or video_prefix is a valid
    """
    if len(the_id) == 20 or len(the_id) == 24:
        if the_id[12] == "-":
            if len(the_id) == 24 and the_id[20] == "_":
                return True
            elif len(the_id) == 20:
                return True
            else:
                return False
        else:
            return False
    else:
        return False







