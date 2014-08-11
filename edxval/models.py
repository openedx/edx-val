"""
Django models for videos for Video Abstraction Layer (VAL)
"""

from django.db import models
from django.core.validators import MinValueValidator, RegexValidator


class Profile(models.Model):
    """
    Details for pre-defined encoding format
    """
    profile_name = models.CharField(
        max_length=50,
        unique=True,
    )
    extension = models.CharField(max_length=10)
    width = models.PositiveIntegerField()
    height = models.PositiveIntegerField()


class Video(models.Model):
    """
    Model for a Video group with the same content.

    A video can have multiple formats. This model are the fields that represent
    the collection of those videos that do not change across formats.
    """
    edx_video_id = models.CharField(
        max_length=50,
        unique=True,
        validators=[
            RegexValidator(
                regex='^[a-zA-Z0-9\-]*$',
                message='edx_video_id has invalid characters',
                code='invalid edx_video_id'
            ),
        ]
    )
    client_video_id = models.CharField(max_length=255, db_index=True)
    duration = models.FloatField(validators=[MinValueValidator(0)])


class CourseVideos(models.Model):
    """
    Model for the course_id associated with the video content.

    Every course-semester has a unique course_id. A video can be paired with multiple
    course_id's but each pair is unique together.
    """
    course_id = models.CharField(max_length=255)
    video = models.ForeignKey(Video)

    class Meta:
        unique_together = ("course_id", "video")


class EncodedVideo(models.Model):
    """
    Video/encoding pair
    """
    created = models.DateTimeField(auto_now_add=True)
    modified = models.DateTimeField(auto_now=True)
    url = models.URLField(max_length=200)
    file_size = models.PositiveIntegerField()
    bitrate = models.PositiveIntegerField()

    profile = models.ForeignKey(Profile, related_name="+")
    video = models.ForeignKey(Video, related_name="encoded_videos")
