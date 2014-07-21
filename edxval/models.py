"""
Django models for videos for Video Abstraction Layer (VAL)
"""

from django.db import models


class Profile(models.Model):
    """
    Details for pre-defined encoding format
    """
    profile_name = models.CharField(max_length=50, unique=True)
    extension = models.CharField(max_length=10)
    width = models.PositiveIntegerField()
    height = models.PositiveIntegerField()

    def __repr__(self):
        return (
            u"Profile(profile_name={0.profile_name})"
        ).format(self)

    def __unicode__(self):
        return repr(self)


class Video(models.Model):
    """
    Model for a Video group with the same content.

    A video can have multiple formats. This model is the collection of those
    videos with fields that do not change across formats.
    """
    edx_video_id = models.CharField(max_length=50, unique=True)
    client_title = models.CharField(max_length=255, db_index=True)
    duration = models.FloatField()

    def __repr__(self):
        return (
            u"Video(client_title={0.client_title}, duration={0.duration})"
        ).format(self)

    def __unicode__(self):
        return repr(self)


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

    def __repr__(self):
        return (
            u"EncodedVideo(video={0.video.client_title}, "
            u"profile={0.profile.profile_name})"
        ).format(self)

    def __unicode__(self):
        return repr(self)
