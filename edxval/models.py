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

import json
import logging
import os
from contextlib import closing
from uuid import uuid4

from django.core.exceptions import ValidationError
from django.core.urlresolvers import reverse
from django.core.validators import MinValueValidator, RegexValidator
from django.db import models
from django.dispatch import receiver
from django.utils.six import python_2_unicode_compatible
from model_utils.models import TimeStampedModel

from edxval.utils import (get_video_image_storage,
                          get_video_transcript_storage, video_image_path,
                          video_transcript_path)

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


@python_2_unicode_compatible
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

    def __str__(self):
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
        ).prefetch_related('encoded_videos', 'courses')
        return qset


@python_2_unicode_compatible
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

    def __str__(self):
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
    def __init__(self, max_items=LIST_MAX_ITEMS, *args, **kwargs):
        self.max_items = max_items
        super(ListField, self).__init__(*args, **kwargs)

    def get_prep_value(self, value):
        """
        Converts a list to its json representation to store in database as text.
        """
        if value and not isinstance(value, list):
            raise ValidationError(u'ListField value {} is not a list.'.format(value))
        return json.dumps(self.validate_list(value) or [])

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
            py_list = self.validate_list(value)
        else:  # try to de-serialize value and expect list and then validate
            try:
                py_list = json.loads(value)

                if not isinstance(py_list, list):
                    raise TypeError

                self.validate_list(py_list)
            except (ValueError, TypeError):
                raise ValidationError(u'Must be a valid list of strings.')

        return py_list

    def validate_list(self, value):
        """
        Validate data before saving to database.

        Arguemtns:
            value(list): list to be validated

        Returns:
            list if validation is successful

        Raises:
            ValidationError
        """
        if len(value) > self.max_items:
            raise ValidationError(
                u'list must not contain more than {max_items} items.'.format(max_items=self.max_items)
            )

        if all(isinstance(item, basestring) for item in value) is False:
            raise ValidationError(u'list must only contain strings.')

        return value

    def deconstruct(self):
        name, path, args, kwargs = super(ListField, self).deconstruct()
        # Only include kwarg if it's not the default
        if self.max_items != LIST_MAX_ITEMS:
            kwargs['max_items'] = self.max_items
        return name, path, args, kwargs


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


class TranscriptProviderType(object):
    CUSTOM = 'Custom'
    THREE_PLAY_MEDIA = '3PlayMedia'
    CIELO24 = 'Cielo24'

    CHOICES = (
        (CUSTOM, CUSTOM),
        (THREE_PLAY_MEDIA, THREE_PLAY_MEDIA),
        (CIELO24, CIELO24),
    )


class TranscriptFormat(object):
    SRT = 'srt'
    SJSON = 'sjson'

    CHOICES = (
        (SRT, 'SubRip'),
        (SJSON, 'SRT JSON')
    )


class CustomizableFileField(models.FileField):
    """
    Subclass of FileField that allows custom settings to not
    be serialized (hard-coded) in migrations. Otherwise,
    migrations include optional settings for storage (such as
    the storage class and bucket name); we don't want to
    create new migration files for each configuration change.
    """
    def __init__(self, *args, **kwargs):
        kwargs.update(dict(
            upload_to=video_transcript_path,
            storage=get_video_transcript_storage(),
            max_length=255,  # enoungh for uuid
            blank=True,
            null=True
        ))
        super(CustomizableFileField, self).__init__(*args, **kwargs)

    def deconstruct(self):
        """
        Override base class method.
        """
        name, path, args, kwargs = super(CustomizableFileField, self).deconstruct()
        del kwargs['upload_to']
        del kwargs['storage']
        del kwargs['max_length']
        return name, path, args, kwargs


class VideoTranscript(TimeStampedModel):
    """
    Transcript for a video
    """
    video_id = models.CharField(max_length=255, help_text='It can be an edx_video_id or an external video id')
    transcript = CustomizableFileField()
    language_code = models.CharField(max_length=50, db_index=True)
    provider = models.CharField(
        max_length=30,
        choices=TranscriptProviderType.CHOICES,
        default=TranscriptProviderType.CUSTOM,
    )
    file_format = models.CharField(max_length=20, db_index=True, choices=TranscriptFormat.CHOICES)

    class Meta:
        unique_together = ('video_id', 'language_code')

    @classmethod
    def get_or_none(cls, video_id, language_code):
        """
        Returns a data model object if found or none otherwise.

        Arguments:
            video_id(unicode): video id to which transcript may be associated
            language_code(unicode): language of the requested transcript
        """
        try:
            transcript = cls.objects.get(video_id=video_id, language_code=language_code)
        except cls.DoesNotExist:
            transcript = None

        return transcript

    @classmethod
    def create_or_update(cls, video_id, language_code, file_name, file_format, provider, file_data=None):
        """
        Create or update Transcript object.

        Arguments:
            video_id (str): unique id for a video
            language_code (str): language code
            file_name (str): File name of the image
            file_format (str): Format of transcript
            provider (str): Transcript provider
            file_data (InMemoryUploadedFile): File data to be saved

        Returns:
            Returns a tuple of (video_transcript, created).
        """
        video_transcript, created = cls.objects.get_or_create(video_id=video_id, language_code=language_code)

        # delete the existing transcript file
        if not created and file_data:
            video_transcript.transcript.delete()

        video_transcript.transcript.name = file_name
        video_transcript.file_format = file_format
        video_transcript.provider = provider

        if file_data:
            with closing(file_data) as transcript_file_data:
                file_name = '{uuid}{ext}'.format(uuid=uuid4().hex, ext=os.path.splitext(file_name)[1])
                try:
                    video_transcript.transcript.save(file_name, transcript_file_data)
                except Exception:  # pylint: disable=broad-except
                    logger.exception('VAL: Transcript save failed to storage for video_id [%s]', video_id)
                    raise

        video_transcript.save()
        return video_transcript, created

    def url(self):
        """
        Returns language transcript url for a particular language.
        """
        storage = get_video_transcript_storage()
        return storage.url(self.transcript.name)

    def __unicode__(self):
        return u'{lang} Transcript for {video}'.format(lang=self.language_code, video=self.video_id)


class Cielo24Turnaround(object):
    """
    Cielo24 turnarounds.
    """
    STANDARD = 'STANDARD'
    PRIORITY = 'PRIORITY'
    CHOICES = (
        (STANDARD, 'Standard, 48h'),
        (PRIORITY, 'Priority, 24h'),
    )


class Cielo24Fidelity(object):
    """
    Cielo24 fidelity.
    """
    MECHANICAL = 'MECHANICAL'
    PREMIUM = 'PREMIUM'
    PROFESSIONAL = 'PROFESSIONAL'
    CHOICES = (
        (MECHANICAL, 'Mechanical, 75% Accuracy'),
        (PREMIUM, 'Premium, 95% Accuracy'),
        (PROFESSIONAL, 'Professional, 99% Accuracy'),
    )


class ThreePlayTurnaround(object):
    """
    3PlayMedia turnarounds.
    """
    EXTENDED_SERVICE = 'extended_service'
    DEFAULT = 'default'
    EXPEDITED_SERVICE = 'expedited_service'
    RUSH_SERVICE = 'rush_service'
    SAME_DAY_SERVICE = 'same_day_service'

    CHOICES = (
        (EXTENDED_SERVICE, '10-Day/Extended'),
        (DEFAULT, '4-Day/Default'),
        (EXPEDITED_SERVICE, '2-Day/Expedited'),
        (RUSH_SERVICE, '24 hour/Rush'),
        (SAME_DAY_SERVICE, 'Same Day'),
    )


class TranscriptPreference(TimeStampedModel):
    """
    Third Party Transcript Preferences for a Course
    """
    course_id = models.CharField(verbose_name='Course ID', max_length=255, unique=True)
    provider = models.CharField(
        verbose_name='Provider',
        max_length=20,
        choices=TranscriptProviderType.CHOICES,
    )
    cielo24_fidelity = models.CharField(
        verbose_name='Cielo24 Fidelity',
        max_length=20,
        choices=Cielo24Fidelity.CHOICES,
        null=True,
        blank=True,
    )
    cielo24_turnaround = models.CharField(
        verbose_name='Cielo24 Turnaround',
        max_length=20,
        choices=Cielo24Turnaround.CHOICES,
        null=True,
        blank=True,
    )
    three_play_turnaround = models.CharField(
        verbose_name='3PlayMedia Turnaround',
        max_length=20,
        choices=ThreePlayTurnaround.CHOICES,
        null=True,
        blank=True,
    )
    preferred_languages = ListField(verbose_name='Preferred Languages', max_items=50, default=[], blank=True)
    video_source_language = models.CharField(
        verbose_name='Video Source Language',
        max_length=50,
        null=True,
        blank=True,
        help_text='This specifies the speech language of a Video.'
    )

    def __unicode__(self):
        return u'{course_id} - {provider}'.format(course_id=self.course_id, provider=self.provider)


class ThirdPartyTranscriptCredentialsState(TimeStampedModel):
    """
    State of transcript credentials for a course organization
    """
    class Meta:
        unique_together = ('org', 'provider')

    org = models.CharField(verbose_name='Course Organization', max_length=32)
    provider = models.CharField(
        verbose_name='Transcript Provider',
        max_length=20,
        choices=TranscriptProviderType.CHOICES,
    )
    exists = models.BooleanField(default=False, help_text='Transcript credentials state')

    @classmethod
    def update_or_create(cls, org, provider, exists):
        """
        Update or create credentials state.
        """
        instance, created = cls.objects.update_or_create(
            org=org,
            provider=provider,
            defaults={'exists': exists},
        )

        return instance, created

    def __unicode__(self):
        """
        Returns unicode representation of provider credentials state for an organization.

        NOTE: Message will look like below:
            edX has Cielo24 credentials
            edX doesn't have 3PlayMedia credentials
        """
        return u'{org} {state} {provider} credentials'.format(
            org=self.org, provider=self.provider, state='has' if self.exists else "doesn't have"
        )


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
