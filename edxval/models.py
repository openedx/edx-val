"""
Django models for videos for Video Abstraction Layer (VAL)
"""

from django.db import models


class Video(models.Model):
    """
    Model for a Video group with the same content.

    A video can have multiple formats. This model is the collection of those
    videos with fields that do not change across formats.

    """
    title = models.CharField(max_length=255, db_index=True)
    duration = models.FloatField()
    edx_video_id = models.CharField(max_length=50, unique=True)


    def __repr__(self):
        return (
            u"Video(title={0.title}, duration={0.duration})"
        ).format(self)

    def __unicode__(self):
        return repr(self)


class Profile(models.Model):
    """
    Details for pre-defined encoding format
    """
    profile_id = models.CharField(max_length=50, unique=True)
    profile_name = models.CharField(max_length=50, unique=True)
    extension = models.CharField(max_length=50)
    width = models.PositiveIntegerField()
    height = models.PositiveIntegerField()
    bitrate = models.PositiveIntegerField()

    def __repr__(self):
        return (
            u"Profile(title={0.profile_id}, "
            u"profile_name={0.profile_name}, "
            u"extension={0.extension}, width={0.width}, "
            u"height={0.height}, bitrate={0.bitrate})"
        ).format(self)

    def __unicode__(self):
        return repr(self)


class EncodedVideo(models.Model):
    """
    Unique video/encoding pair
    """
    title = models.CharField(max_length=255, db_index=True)
    created = models.DateTimeField(auto_now_add=True)
    modified = models.DateTimeField(auto_now=True)
    url = models.URLField(max_length=200)
    file_size = models.PositiveIntegerField()
    profile = models.ForeignKey(Profile)
    video = models.ForeignKey(Video)

    def __repr__(self):
        return (
            u"EncodedVideo(video={0.video.title}, "
            u"profile={0.profile.profile_id} "
            u"title={0.title})"
        ).format(self)

    def __unicode__(self):
        return repr(self)
