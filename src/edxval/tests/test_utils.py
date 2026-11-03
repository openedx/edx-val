# -*- coding: utf-8 -*-
"""
Tests the utilities for the Video Abstraction Layer
"""
from django.core.files.base import ContentFile
from django.test import TestCase

from edxval.utils import generate_file_content_hash, is_duplicate_file


class UtilityTests(TestCase):
    """
    Tests utility methods
    """
    def test_generate_file_content_hash(self):
        """
        Tests generating file content hash and makes sure the hash returned is
        64 characters long
        """
        file_data = ContentFile('Greetings')

        content_hash = generate_file_content_hash(file_data)

        self.assertEqual(len(content_hash), 64)

    def test_same_content_is_duplicate_file(self):
        """
        Tests the `is_duplicate_file` by generating a hash for a content file
        and then passing the hash and the content to the method to make sure
        that the 'files' are the same/duplicates.
        """
        file_content = 'Greetings'

        file_data = ContentFile(file_content)
        other_file_data = ContentFile(file_content)

        self.assertTrue(is_duplicate_file(file_data, other_file_data))

    def test_different_content_is_duplicate_file(self):
        """
        Tests the `is_duplicate_file` by generating a hash for a content file
        and then passing the hash and the different file content to the method
        to make sure that the 'files' are the different.
        """
        file_content = 'Greetings'
        other_file_content = 'Hello there'

        file_data = ContentFile(file_content)
        other_file_data = ContentFile(other_file_content)

        self.assertFalse(is_duplicate_file(file_data, other_file_data))
