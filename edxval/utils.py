"""
Util methods to be used in api and models.
"""

from django.conf import settings
from django.core.files.storage import get_storage_class


def _create_path(directory, filename):
    """
    Returns the full path for the given directory and filename.
    """
    return '{}-{}'.format(directory, filename)


def _directory_name(edx_video_id):
    """
    Returns the directory name for the given edx_video_id.
    """
    return '{}{}'.format(settings.VIDEO_IMAGE_SETTINGS.get('DIRECTORY_PREFIX', ''), edx_video_id)


def video_image_path_name(image_model, filename):  # pylint:disable=unused-argument
    """
    Returns path name to use for the given Video instance.
    """
    return _create_path(_directory_name(image_model.video.edx_video_id), filename)


def get_video_image_storage():
    """
    Return the configured django storage backend.
    """
    return get_storage_class(
         settings.VIDEO_IMAGE_SETTINGS.get('STORAGE_CLASS'),
    )(**settings.VIDEO_IMAGE_SETTINGS.get('STORAGE_KWARGS', {}))


