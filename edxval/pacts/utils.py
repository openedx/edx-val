"""
Utility methods needed during pact verification.
"""

from edxval.models import CourseVideo, EncodedVideo, Profile, Video, VideoImage, VideoTranscript
from edxval.tests import constants

VIDEO_ID = "3386eda1-8d6e-439d-tb89-e90a5c52h103"
COURSE_ID = "course-v1:testX+test123+2030"
DEFAULT_PROFILE_NAMES = ['desktop_mp4', 'mobile_low', 'mp3', 'hls']


def clear_database():
    """
    Helper method to clear the database before a pact interaction
    to make sure that no existing data causes issue during pact verification.
    """
    CourseVideo.objects.filter(course_id=COURSE_ID, video__edx_video_id=VIDEO_ID).delete()
    Profile.objects.filter(profile_name__in=DEFAULT_PROFILE_NAMES).delete()
    Video.objects.filter(edx_video_id=VIDEO_ID).delete()
    EncodedVideo.objects.filter(video__edx_video_id=VIDEO_ID).delete()
    VideoImage.objects.filter(course_video__video__edx_video_id=VIDEO_ID).delete()
    VideoTranscript.objects.filter(video__edx_video_id=VIDEO_ID).delete()


def setup_successful_video_details_state():
    """
    Setup the provider state for successful video details update call.
    """
    create_course_video()
    create_profiles()


def setup_unsuccessful_video_transcripts_state():
    """
    Setup the provider state for unsuccessful video transcripts update call.
    """
    video = create_video()
    VideoTranscript.objects.create(video=video, language_code='en', provider='3PlayMedia', file_format='sjson')


def create_video():
    """
    Creates and return a new video object with pre-defined data.
    """
    data_dict = {** constants.VIDEO_DICT_FISH, 'edx_video_id': VIDEO_ID}
    return Video.objects.create(**data_dict)


def create_profiles():
    """
    Create and return a list of default profiles created.
    """
    profiles = []
    for profile_name in DEFAULT_PROFILE_NAMES:
        profiles.append(Profile.objects.create(profile_name=profile_name))
    return profiles


def create_course_video():
    """
    Creates and return a new video object with pre-defined data.
    """
    video = create_video()
    return CourseVideo.objects.create(course_id=COURSE_ID, video=video)
