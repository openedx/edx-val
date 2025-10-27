
"""
Unit tests for django-storages
"""

from unittest import TestCase

from django.conf import settings
from django.test.utils import override_settings

from edxval.utils import get_video_image_storage, get_video_transcript_storage
from storages.backends.s3boto3 import S3Boto3Storage  # pylint: disable=wrong-import-order


class S3Boto3TestCase(TestCase):
    """Unit tests for verifying the S3Boto3 storage backend selection logic"""

    def setUp(self):
        self.storage = S3Boto3Storage()

    def test_video_image_backend(self):
        # settings file contains the `VIDEO_IMAGE_SETTINGS` but dont'have STORAGE_CLASS
        # so it returns the default storage.

        storage = get_video_image_storage()
        storage_class = storage.__class__

        self.assertEqual(
            'django.core.files.storage.filesystem.FileSystemStorage',
            f"{storage_class.__module__}.{storage_class.__name__}",
        )

    @override_settings(VIDEO_IMAGE_SETTINGS={
        'STORAGE_CLASS': 'storages.backends.s3boto3.S3Boto3Storage',
        'STORAGE_KWARGS': {
            'bucket_name': 'test',
            'default_acl': 'public',
            'location': 'abc/def'
        }
    })
    def test_video_image_backend_with_params(self):
        storage = get_video_image_storage()
        self.assertIsInstance(storage, S3Boto3Storage)
        self.assertEqual(storage.bucket_name, "test")
        self.assertEqual(storage.default_acl, 'public')
        self.assertEqual(storage.location, "abc/def")

    def test_video_image_without_storages_settings(self):
        # Remove VIDEO_IMAGE_SETTINGS from settings safely
        if hasattr(settings, 'VIDEO_IMAGE_SETTINGS'):
            del settings.VIDEO_IMAGE_SETTINGS

        storage = get_video_image_storage()
        storage_class = storage.__class__

        self.assertEqual(
            'django.core.files.storage.filesystem.FileSystemStorage',
            f"{storage_class.__module__}.{storage_class.__name__}",
        )

    def test_video_transcript_backend(self):
        # settings file contains the `VIDEO_TRANSCRIPTS_SETTINGS` but dont'have STORAGE_CLASS
        # so it returns the default storage.

        storage = get_video_transcript_storage()
        storage_class = storage.__class__

        self.assertEqual(
            'django.core.files.storage.filesystem.FileSystemStorage',
            f"{storage_class.__module__}.{storage_class.__name__}",
        )

    @override_settings(VIDEO_TRANSCRIPTS_SETTINGS={
        'STORAGE_CLASS': 'storages.backends.s3boto3.S3Boto3Storage',
        'STORAGE_KWARGS': {
            'bucket_name': 'test',
            'default_acl': 'private',
            'location': 'abc/'
        }
    })
    def test_transcript_storage_backend_with_params(self):
        storage = get_video_transcript_storage()
        self.assertIsInstance(storage, S3Boto3Storage)
        self.assertEqual(storage.bucket_name, "test")
        self.assertEqual(storage.default_acl, 'private')
        self.assertEqual(storage.location, 'abc/')

    def test_video_transcript_without_storages_settings(self):
        # Remove VIDEO_TRANSCRIPTS_SETTINGS from settings.
        if hasattr(settings, 'VIDEO_TRANSCRIPTS_SETTINGS'):
            del settings.VIDEO_TRANSCRIPTS_SETTINGS

        storage = get_video_transcript_storage()
        storage_class = storage.__class__

        self.assertEqual(
            'django.core.files.storage.filesystem.FileSystemStorage',
            f"{storage_class.__module__}.{storage_class.__name__}",
        )

    @override_settings(VIDEO_TRANSCRIPTS_SETTINGS={
        'STORAGE_KWARGS': {
            'location': 'only/kwargs/'
        }
    })
    def test_video_transcript_with_storage_kwargs_only(self):
        """
        Test case where STORAGE_CLASS is not defined but STORAGE_KWARGS is defined.
        """
        storage = get_video_transcript_storage()
        storage_class = storage.__class__

        self.assertEqual(
            'django.core.files.storage.filesystem.FileSystemStorage',
            f"{storage_class.__module__}.{storage_class.__name__}",
        )

        self.assertEqual(storage.base_location, 'only/kwargs/')

    @override_settings(
        VIDEO_TRANSCRIPTS_SETTINGS={
            'STORAGE_KWARGS': {
                'bucket_name': 'test-bucket',
                'default_acl': 'private',
                'location': 'only/kwargs/',
            }
        },
        DEFAULT_FILE_STORAGE='storages.backends.s3boto3.S3Boto3Storage'
    )
    def test_video_transcript_with_storage_kwargs_only_and_default_storage(self):
        """
        Test case where STORAGE_CLASS is not defined but STORAGE_KWARGS is defined
        and DEFAULT_FILE_STORAGE is set to S3Boto3Storage in settings.
        """
        storage = get_video_transcript_storage()

        self.assertIsInstance(storage, S3Boto3Storage)
        self.assertEqual(storage.default_acl, 'private')
        self.assertEqual(storage.bucket_name, 'test-bucket')
        self.assertEqual(storage.location, 'only/kwargs/')
