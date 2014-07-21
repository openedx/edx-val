"""
Django models for videos for Video Abstraction Layer (VAL)
"""

from django.db import models


class Profile(models.Model):
    """
    Details for pre-defined encoding format
    """
    profile_id = models.CharField(max_length=50, unique=True)
    profile_name = models.CharField(max_length=50, unique=True)
    extension = models.CharField(max_length=50)
    width = models.PositiveIntegerField()
    height = models.PositiveIntegerField()

    def __repr__(self):
        return (
            u"Profile(profile_id={0.profile_id}, "
            u"profile_name={0.profile_name})"
        ).format(self)

    def __unicode__(self):
        return repr(self)

#TODO create Course_id model


class Video(models.Model):
    """
    Model for a Video group with the same content.

    A video can have multiple formats. This model is the collection of those
    videos with fields that do not change across formats.
    """
    video_prefix = models.CharField(max_length=50, unique=True)
    client_title = models.CharField(max_length=255, db_index=True)
    duration = models.FloatField()
    #TODO Create relationship to Course_id model

    def __repr__(self):
        return (
            u"Video(client_title={0.client_title}, duration={0.duration})"
        ).format(self)

    def __unicode__(self):
        return repr(self)


class EncodedVideo(models.Model):
    """
    Video/encoding pair
    """
    edx_video_id = models.CharField(max_length=50, unique=True)
    created = models.DateTimeField(auto_now_add=True)
    modified = models.DateTimeField(auto_now=True)
    url = models.URLField(max_length=200)
    file_size = models.PositiveIntegerField()
    bitrate = models.PositiveIntegerField()

    profile = models.ForeignKey(Profile)
    video = models.ForeignKey(Video, related_name="encoded_video")

    def __repr__(self):
        return (
            u"EncodedVideo(edx_video_id={0.edx_video_id}, "
            u"video={0.video.client_title}, "
            u"profile={0.profile.profile_id})"
        ).format(self)

    def __unicode__(self):
        return "{0}:{1}".format(self.edx_video_id, self.url)
