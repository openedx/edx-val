"""
Util methods to be used in api and models.
"""

from django.conf import settings
from django.core.files.storage import get_storage_class


def video_image_path(video_image_instance, filename):  # pylint:disable=unused-argument
    """
    Returns video image path.

    Arguments:
        video_image_instance (VideoImage): This is passed automatically by models.CustomizableImageField
        filename (str): name of image file
    """
    return u'{}{}'.format(settings.VIDEO_IMAGE_SETTINGS.get('DIRECTORY_PREFIX', ''), filename)


def get_video_image_storage():
    """
    Return the configured django storage backend.
    """
    if hasattr(settings, 'VIDEO_IMAGE_SETTINGS'):
        return get_storage_class(
            settings.VIDEO_IMAGE_SETTINGS.get('STORAGE_CLASS'),
        )(**settings.VIDEO_IMAGE_SETTINGS.get('STORAGE_KWARGS', {}))
    else:
        # during edx-platform loading this method gets called but settings are not ready yet
        # so in that case we will return default(FileSystemStorage) storage class instance
        return get_storage_class()()
