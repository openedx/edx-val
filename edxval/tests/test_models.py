# -*- coding: utf-8 -*-
""" Test for models """


from django.test import TestCase

from edxval.models import CourseVideo, Video, VideoImage, VideoTranscript
from edxval.tests import constants


class VideoTranscriptTest(TestCase):
    """
    Test VideoTranscript model
    """

    def setUp(self):
        """
        Creates Profile objects and a video object
        """
        self.transcript_data = constants.VIDEO_TRANSCRIPT_CIELO24
        super(VideoTranscriptTest, self).setUp()

    def test_filename_property_new_line(self):
        """
        Test that filename does not contain any "\n".
        New line is not permmited in response headers.
        """
        video = Video.objects.create(**constants.VIDEO_DICT_NEW_LINE)
        video_trancript = VideoTranscript.objects.create(
            video=video,
            language_code=self.transcript_data['language_code'],
            file_format=self.transcript_data['file_format'],
            provider=self.transcript_data['provider'],
        )

        self.assertNotIn('\n', video_trancript.filename)
        assert str(video_trancript) == "en Transcript for new-line-not-allowed"


class VideoImageTest(TestCase):
    """
    Tests for VideoImage model.
    """

    def setUp(self):
        """
        Create Video and VideoImage object
        """
        super(VideoImageTest, self).setUp()
        course_id = 'test-course'
        video = Video.objects.create(**constants.VIDEO_DICT_NEW_LINE)

        self.course_video = CourseVideo.objects.create(video=video, course_id=course_id)
        self.video_image = VideoImage.objects.create(course_video=self.course_video)
        self.generated_images = ['test-thumbnail-1.jpeg', 'test-thumbnail-2.jpeg']

    def test_generated_images_when_no_image_exists(self):
        """
        Test that if generated_images of video image are updated when no previous
        manual upload exists, then first generated_image is set as the thumbnail.
        """
        video_image, _ = VideoImage.create_or_update(self.course_video, generated_images=self.generated_images)
        self.assertEqual(video_image.image, self.generated_images[0])

    def test_generated_images_when_image_exists(self):
        """
        Test that if generated_images of video image are updated when previous
        manual upload exists, then image field does not change.
        """
        manually_uploaded_img = 'manual-upload.jpeg'
        self.video_image.image = manually_uploaded_img
        self.video_image.save()

        video_image, _ = VideoImage.create_or_update(self.course_video, generated_images=self.generated_images)
        self.assertNotEqual(video_image.image, self.generated_images[0])
        self.assertEqual(video_image.image, manually_uploaded_img)
