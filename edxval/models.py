"""
Django models for videos for Video Abstraction Layer (VAL)

When calling a serializers' .errors function for objects, there is an
order in which the errors are returned. This may cause a partial return of errors

Example:
class Profile(models.Model)
    profile_name = models.CharField(
        max_length=50,
        unique=True,
        validators=[
            RegexValidator(
                regex=r'^[a-zA-Z0-9\-]*$',
                message='profile_name has invalid characters',
                code='invalid profile_name'
            ),
        ]
    )
    extension = models.CharField(max_length=10)
    width = models.PositiveIntegerField()
    height = models.PositiveIntegerField()

Missing a field, having an input type (expected an int, not a str),
nested serialization errors, or any similar errors will be returned by
themselves. After these are resolved, errors such as a negative height, or
invalid profile_name will be returned.
"""

from django.db import models
from django.core.validators import MinValueValidator, RegexValidator
from django.core.urlresolvers import reverse


url_regex = r'^[a-zA-Z0-9\-]*$'


class Profile(models.Model):
    """
    Details for pre-defined encoding format

    The profile_name has a regex validator because in case this field will be
    used in a url.
    """
    profile_name = models.CharField(
        max_length=50,
        unique=True,
        validators=[
            RegexValidator(
                regex=url_regex,
                message='profile_name has invalid characters',
                code='invalid profile_name'
            ),
        ]
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
                regex=url_regex,
                message='edx_video_id has invalid characters',
                code='invalid edx_video_id'
            ),
        ]
    )
    client_video_id = models.CharField(max_length=255, db_index=True)
    duration = models.FloatField(validators=[MinValueValidator(0)])

    def __str__(self):
        return self.edx_video_id


class CourseVideos(models.Model):
    """
    Model for the course_id associated with the video content.

    Every course-semester has a unique course_id. A video can be paired with multiple
    course_id's but each pair is unique together.
    """
    course_id = models.CharField(max_length=255)
    video = models.ForeignKey(Video)

    class Meta:  # pylint: disable=C1001
        """
        course_id is listed first in this composite index
        """
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


SUBTITLE_FORMATS = (
    ('srt', 'SubRip'),
    ('sjson', 'SRT JSON')
)


class Subtitle(models.Model):
    """
    Subtitle for video
    """
    created = models.DateTimeField(auto_now_add=True)
    modified = models.DateTimeField(auto_now=True)
    video = models.ForeignKey(Video, related_name="subtitles")
    fmt = models.CharField(max_length=20, db_index=True, choices=SUBTITLE_FORMATS)
    language = models.CharField(max_length=8, db_index=True)
    content = models.TextField()

    def __str__(self):
        return '%s Subtitle for %s' % (self.language, self.video)

    def get_absolute_url(self):
        return reverse('subtitle-content', args=[str(self.id)])

    @property
    def content_type(self):
        if self.fmt == 'sjson':
            return 'application/json'
        else:
            return 'text/plain'
