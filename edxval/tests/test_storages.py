"""
Unit tests for video utils.
"""

from unittest import TestCase, mock

from django.conf import settings
from django.test.utils import override_settings

from edxval.utils import get_video_image_storage, get_video_transcript_storage
from storages.backends.s3boto3 import S3Boto3Storage


class S3Boto3TestCase(TestCase):
    """Unit tests for verifying the S3Boto3 storage backend selection logic."""

    def setUp(self):
        self.storage = S3Boto3Storage()
        self.storage._connections.connection = mock.MagicMock()  # Avoid AWS calls

    def test_video_image_backend(self):
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
        # Remove STORAGES from settings safely
        if hasattr(settings, 'STORAGES'):
            del settings.STORAGES

        storage = get_video_image_storage()
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