"""
Django models for videos for Video Abstration Layer (VAL)
"""

from django.db import models
import django.utils.timezone as timezone

class AutoDateTimeField(models.DateTimeField):
    """
    Custom field for datetime creation/modification

    """
    def pre_save(self, model_instance, add):
        return timezone.now()

class Video(models.Model):
    """
    A single version of a video file

    A video can have multiple versions (mobile, HQ, LQ, ...). Each version has
    its own edx_uid.

    """
    edx_uid = models.CharField(max_length=50, unique=True)
    title = models.CharField(max_length=255, db_index=True)
    created = models.DateTimeField(default=timezone.now())
    updated = AutoDateTimeField(default=timezone.now())

    print timezone.now()

    def __repr__(self):
        return (
            "Video(edx_uid={0.edx_uid}, title={0.title}, "
            "created={0.created}, updated={0.created}"
        ).format(self)

    def __unicode__(self):
        return repr(self)

class Profile(models.Model):
    """
    Details for pre-defined encoding format
    """
    title = models.CharField(max_length=50, unique=True)
    name = models.CharField(max_length=50, unique=True)
    extension = models.CharField(max_length=50)
    width = models.PositiveIntegerField()
    height = models.PositiveIntegerField()
    bitrate = models.PositiveIntegerField()

    def get_resolution(self):
        return str(self.width) + "x" + str(self.height)

    def __repr__(self):
        return (
            "Profile(title={0.title}, name={0.name}, "
            "extension={0.extension}, width={0.width}, "
            "height={0.height}, bitrate={0.bitrate})"
        ).format(self)

    def __unicode__(self):
        return repr(self)


class Encoding(models.Model):
    """
    Video and encoding profile pair
    """
    video = models.ForeignKey(Video)
    profile = models.ForeignKey(Profile)
    file_size = models.PositiveIntegerField()
    duration = models.FloatField()

    def __repr__(self):
        return (
            "Encoding(video={0.video}, profile={0.profile}, "
            "file_size={0.file_size}, duration={0.duration})"
        ).format(self)

    def __unicode__(self):
        return repr(self)