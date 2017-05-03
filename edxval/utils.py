"""
Util methods to be used in api and models.
"""

from django.conf import settings
from django.core.files.storage import get_storage_class


def video_image_path(video_image_instance, filename):  # pylint:disable=unused-argument
    """
    Returns video image path.
    """
    return '{}{}'.format(settings.VIDEO_IMAGE_SETTINGS.get('DIRECTORY_PREFIX', ''), filename)


def get_video_image_storage():
    """
    Return the configured django storage backend.
    """
    if hasattr(settings, 'VIDEO_IMAGE_SETTINGS'):
        return get_storage_class(
            settings.VIDEO_IMAGE_SETTINGS.get('STORAGE_CLASS'),
        )(**settings.VIDEO_IMAGE_SETTINGS.get('STORAGE_KWARGS', {}))
    else:
        return get_storage_class()
