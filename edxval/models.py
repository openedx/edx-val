"""
Django models for videos for Video Abstraction Layer (VAL)

When calling a serializers' .errors field, there is a priority in which the
errors are returned. This may cause a partial return of errors, starting with
the highest priority.

Missing a field, having an incorrect input type (expected an int, not a str),
nested serialization errors, or any similar errors will be returned by
themselves. After these are resolved, errors such as a negative file_size or
invalid profile_name will be returned.
"""

from contextlib import closing
import json
import logging
import os
from uuid import uuid4

from django.db import models
from django.dispatch import receiver
from django.core.exceptions import ValidationError
from django.core.validators import MinValueValidator, RegexValidator
from django.core.urlresolvers import reverse

from model_utils.models import TimeStampedModel

from edxval.utils import video_image_path, get_video_image_storage

logger = logging.getLogger(__name__)  # pylint: disable=C0103

URL_REGEX = r'^[a-zA-Z0-9\-_]*$'
LIST_MAX_ITEMS = 3


class ModelFactoryWithValidation(object):
    """
    A Model mixin that provides validation-based factory methods.
    """
    @classmethod
    def create_with_validation(cls, *args, **kwargs):
        """
        Factory method that creates and validates the model object before it is saved.
        """
        ret_val = cls(*args, **kwargs)
        ret_val.full_clean()
        ret_val.save()
        return ret_val

    @classmethod
    def get_or_create_with_validation(cls, *args, **kwargs):
        """
        Factory method that gets or creates-and-validates the model object before it is saved.
        Similar to the get_or_create method on Models, it returns a tuple of (object, created),
        where created is a boolean specifying whether an object was created.
        """
        try:
            return cls.objects.get(*args, **kwargs), False
        except cls.DoesNotExist:
            return cls.create_with_validation(*args, **kwargs), True


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
                regex=URL_REGEX,
                message='profile_name has invalid characters',
                code='invalid profile_name'
            ),
        ]
    )

    def __unicode__(self):
        return self.profile_name


class Video(models.Model):
    """
    Model for a Video group with the same content.

    A video can have multiple formats. This model are the fields that represent
    the collection of those videos that do not change across formats.

    Attributes:
        status: Used to keep track of the processing video as it goes through
            the video pipeline, e.g., "Uploading", "File Complete"...
    """
    created = models.DateTimeField(auto_now_add=True)
    edx_video_id = models.CharField(
        max_length=100,
        unique=True,
        validators=[
            RegexValidator(
                regex=URL_REGEX,
                message='edx_video_id has invalid characters',
                code='invalid edx_video_id'
            ),
        ]
    )
    client_video_id = models.CharField(max_length=255, db_index=True, blank=True)
    duration = models.FloatField(validators=[MinValueValidator(0)])
    status = models.CharField(max_length=255, db_index=True)

    def get_absolute_url(self):
        """
        Returns the full url link to the edx_video_id
        """
        return reverse('video-detail', args=[self.edx_video_id])

    def __str__(self):
        return self.edx_video_id

    @classmethod
    def by_youtube_id(cls, youtube_id):
        """
        Look up video by youtube id
        """
        qset = cls.objects.filter(
            encoded_videos__profile__profile_name='youtube',
            encoded_videos__url=youtube_id
        ).prefetch_related('encoded_videos', 'courses', 'subtitles')
        return qset


class CourseVideo(models.Model, ModelFactoryWithValidation):
    """
    Model for the course_id associated with the video content.

    Every course-semester has a unique course_id. A video can be paired with
    multiple course_id's but each pair is unique together.
    """
    course_id = models.CharField(max_length=255)
    video = models.ForeignKey(Video, related_name='courses')
    is_hidden = models.BooleanField(default=False, help_text='Hide video for course.')

    class Meta:  # pylint: disable=C1001
        """
        course_id is listed first in this composite index
        """
        unique_together = ("course_id", "video")

    def image_url(self):
        """
        Return image url for a course video image or None if no image.
        """
        if hasattr(self, 'video_image'):
            return self.video_image.image_url()

    def __unicode__(self):
        return self.course_id


class EncodedVideo(models.Model):
    """
    Video/encoding pair
    """
    created = models.DateTimeField(auto_now_add=True)
    modified = models.DateTimeField(auto_now=True)
    url = models.CharField(max_length=200)
    file_size = models.PositiveIntegerField()
    bitrate = models.PositiveIntegerField()

    profile = models.ForeignKey(Profile, related_name="+")
    video = models.ForeignKey(Video, related_name="encoded_videos")


class CustomizableImageField(models.ImageField):
    """
    Subclass of ImageField that allows custom settings to not
    be serialized (hard-coded) in migrations. Otherwise,
    migrations include optional settings for storage (such as
    the storage class and bucket name); we don't want to
    create new migration files for each configuration change.
    """
    def __init__(self, *args, **kwargs):
        kwargs.update(dict(
            upload_to=video_image_path,
            storage=get_video_image_storage(),
            max_length=500,  # allocate enough for filepath
            blank=True,
            null=True
        ))
        super(CustomizableImageField, self).__init__(*args, **kwargs)

    def deconstruct(self):
        """
        Override base class method.
        """
        name, path, args, kwargs = super(CustomizableImageField, self).deconstruct()
        del kwargs['upload_to']
        del kwargs['storage']
        del kwargs['max_length']
        return name, path, args, kwargs


class ListField(models.TextField):
    """
    ListField use to store and retrieve list data.
    """
    def get_prep_value(self, value):
        """
        Converts a list to its json represetation to store in database as text.
        """
        if value and not isinstance(value, list):
            raise ValidationError(u'ListField value {} is not a list.'.format(value))
        return json.dumps(self.validate(value) or [])

    def from_db_value(self, value, expression, connection, context):
        """
        Converts a json list representation in a database to a python object.
        """
        return self.to_python(value)

    def to_python(self, value):
        """
        Converts the value into a list.
        """
        if not value:
            value = []

        # If a list is set then validated its items
        if isinstance(value, list):
            return self.validate(value)
        else:  # try to de-serialize value and expect list and then validate
            try:
                py_list = json.loads(value)

                if not isinstance(py_list, list):
                    raise TypeError

                self.validate(py_list)
            except (ValueError, TypeError):
                raise ValidationError(u'Must be a valid list of strings.')

        return py_list

    def validate(self, value):
        """
        Validate data before saving to database.

        Arguemtns:
            value(list): list to be validated

        Returns:
            list if validation is successful

        Raises:
            ValidationError
        """
        if len(value) > LIST_MAX_ITEMS:
            raise ValidationError(u'list must not contain more than {} items.'.format(LIST_MAX_ITEMS))

        if all(isinstance(item, basestring) for item in value) is False:
            raise ValidationError(u'list must only contain strings.')

        return value


class VideoImage(TimeStampedModel):
    """
    Image model for course video.
    """
    course_video = models.OneToOneField(CourseVideo, related_name="video_image")
    image = CustomizableImageField()
    generated_images = ListField()

    @classmethod
    def create_or_update(cls, course_video, file_name=None, image_data=None, generated_images=None):
        """
        Create a VideoImage object for a CourseVideo.

        NOTE: If `image_data` is None then `file_name` value will be used as it is, otherwise
        a new file name is constructed based on uuid and extension from `file_name` value.
        `image_data` will be None in case of course re-run and export. `generated_images` list
        contains names of images auto generated by VEDA. If an image is not already set then first
        image name from `generated_images` list will be used.

        Arguments:
            course_video (CourseVideo): CourseVideo instance
            file_name (str): File name of the image
            image_data (InMemoryUploadedFile): Image data to be saved.
            generated_images (list): auto generated image names

        Returns:
            Returns a tuple of (video_image, created).
        """
        video_image, created = cls.objects.get_or_create(course_video=course_video)
        if image_data:
            # Delete the existing image only if this image is not used by anyone else. This is necessary because
            # after a course re-run, a video in original course and the new course points to same image, So when
            # we update an image in new course and delete the existing image. This will delete the image from
            # original course as well, thus leaving video with having no image.
            if not created and VideoImage.objects.filter(image=video_image.image).count() == 1:
                video_image.image.delete()

            with closing(image_data) as image_file:
                file_name = '{uuid}{ext}'.format(uuid=uuid4().hex, ext=os.path.splitext(file_name)[1])
                try:
                    video_image.image.save(file_name, image_file)
                except Exception:  # pylint: disable=broad-except
                    logger.exception(
                        'VAL: Video Image save failed to storage for course_id [%s] and video_id [%s]',
                        course_video.course_id,
                        course_video.video.edx_video_id
                    )
                    raise
        else:
            if generated_images:
                video_image.generated_images = generated_images
                if not video_image.image.name:
                    file_name = generated_images[0]

            video_image.image.name = file_name

        video_image.save()
        return video_image, created

    def image_url(self):
        """
        Return image url for a course video image.
        """
        storage = get_video_image_storage()
        return storage.url(self.image.name)


SUBTITLE_FORMATS = (
    ('srt', 'SubRip'),
    ('sjson', 'SRT JSON')
)


class Subtitle(models.Model):
    """
    Subtitle for video

    Attributes:
        video: the video that the subtitles are for
        fmt: the format of the subttitles file
    """
    created = models.DateTimeField(auto_now_add=True)
    modified = models.DateTimeField(auto_now=True)
    video = models.ForeignKey(Video, related_name="subtitles")
    fmt = models.CharField(max_length=20, db_index=True, choices=SUBTITLE_FORMATS)
    language = models.CharField(max_length=8, db_index=True)
    content = models.TextField(default='')

    def __str__(self):
        return '%s Subtitle for %s' % (self.language, self.video)

    def get_absolute_url(self):
        """
        Returns the full url link to the edx_video_id
        """
        return reverse('subtitle-content', args=[self.video.edx_video_id, self.language])

    @property
    def content_type(self):
        """
        Sjson is returned as application/json, otherwise text/plain
        """
        if self.fmt == 'sjson':
            return 'application/json'
        else:
            return 'text/plain'


@receiver(models.signals.post_save, sender=Video)
def video_status_update_callback(sender, **kwargs):  # pylint: disable=unused-argument
    """
    Log video status for an existing video instance
    """
    video = kwargs['instance']

    if kwargs['created']:
        logger.info('VAL: Video created with id [%s] and status [%s]', video.edx_video_id, video.status)
    else:
        logger.info('VAL: Status changed to [%s] for video [%s]', video.status, video.edx_video_id)
