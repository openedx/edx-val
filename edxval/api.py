"""
The internal API for VAL
"""

from edxval.models import Video, Profile, EncodedVideo
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


def get_video_url(video_format, video_name, location=None):
    """
    Retrieves videos based on parameters

    Args:
        location (str): geographic locations used decide server source
        video_format (str): format of the video (HQ, LQ, mobile, etc)
        video_name (str): name of the video

    Returns:
        result (dict): a dict with the url for specific video
    Raises:
        ValRequestError: Raised if search parameters are not valid
        ValNotAvailableError: Raised if a video format is not available
        ValVideoNotFoundError: Raised if video doesn't exist
        ValInternalError: Raised for unknown errors

    Example:
        >>> get_video_url("location","mobile","CS101-L2-S3")
        {
            'video_url':'www.thevideo.com/fortheCS101classoflecture2sequence3'
        }

    """
    #TODO decide how to handle the parameter types

    if not _valid_profile_id(video_format):
        raise ValRequestError("Unknown video format requested")

    videos = EncodedVideo.objects.filter(title=video_name)

    if not videos:
        error_message = "Error finding video"
        raise ValVideoNotFoundError(error_message)

    try:
        video = videos.get(
            profile=Profile.objects.get(profile_id=video_format))
    except ObjectDoesNotExist:
        error_message = "Format for Video not found"
        raise ValNotAvailableError(error_message)

    result = getattr(video, "url")

    return {
        'url': result
    }


def get_duration(course_id, section, subsection):
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
        ValNotFound: Raised if a parameter is not found
        ValInternalError: Raised for unknown errors
    """
    raise NotImplementedError


def _valid_profile_id(profile_format):
    """
    Checks if the given format is a valid
    """
    valid_formats = ["blqmp4", "mhq3gp", "bhqavi",]
    if profile_format in valid_formats:
        return True
    else:
        return False





