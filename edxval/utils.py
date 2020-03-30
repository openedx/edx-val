"""
Util methods to be used in api and models.
"""

from __future__ import absolute_import

import json

import six
from django.conf import settings
from django.core.exceptions import ValidationError
from django.core.files.storage import get_storage_class
from fs.path import combine
from pysrt import SubRipFile
from rest_framework import status
from rest_framework.response import Response


class TranscriptFormat:
    """Tuple representing transcriptformat choices."""
    SRT = 'srt'
    SJSON = 'sjson'

    CHOICES = (
        (SRT, 'SubRip'),
        (SJSON, 'SRT JSON')
    )


# 3rd Party Transcription Plans
THIRD_PARTY_TRANSCRIPTION_PLANS = {

    'Cielo24': {
        'display_name': 'Cielo24',
        'turnaround': {
            'PRIORITY': 'Priority (24 hours)',
            'STANDARD': 'Standard (48 hours)'
        },
        'fidelity': {
            'MECHANICAL': {
                'display_name': 'Mechanical (75% accuracy)',
                'languages': {
                    'nl': 'Dutch',
                    'en': 'English',
                    'fr': 'French',
                    'de': 'German',
                    'it': 'Italian',
                    'es': 'Spanish',
                }
            },
            'PREMIUM': {
                'display_name': 'Premium (95% accuracy)',
                'languages': {
                    'en': 'English',
                }
            },
            'PROFESSIONAL': {
                'display_name': 'Professional (99% accuracy)',
                'languages': {
                    'ar': 'Arabic',
                    'zh-tw': 'Chinese - Mandarin (Traditional)',
                    'zh-cmn': 'Chinese - Mandarin (Simplified)',
                    'zh-yue': 'Chinese - Cantonese (Traditional)',
                    'nl': 'Dutch',
                    'en': 'English',
                    'fr': 'French',
                    'de': 'German',
                    'he': 'Hebrew',
                    'hi': 'Hindi',
                    'it': 'Italian',
                    'ja': 'Japanese',
                    'ko': 'Korean',
                    'pt': 'Portuguese',
                    'ru': 'Russian',
                    'es': 'Spanish',
                    'tr': 'Turkish',
                }
            },
        }
    },
    '3PlayMedia': {
        'display_name': '3Play Media',
        'turnaround': {
            'two_hour': '2 hours',
            'same_day': 'Same day',
            'rush': '24 hours (rush)',
            'expedited': '2 days (expedited)',
            'standard': '4 days (standard)',
            'extended': '10 days (extended)'
        },
        'languages': {
            'en': 'English',
            'fr': 'French',
            'de': 'German',
            'it': 'Italian',
            'nl': 'Dutch',
            'es': 'Spanish',
            'el': 'Greek',
            'pt': 'Portuguese',
            'zh': 'Chinese',
            'ar': 'Arabic',
            'he': 'Hebrew',
            'ru': 'Russian',
            'ja': 'Japanese',
            'sv': 'Swedish',
            'cs': 'Czech',
            'da': 'Danish',
            'fi': 'Finnish',
            'id': 'Indonesian',
            'ko': 'Korean',
            'no': 'Norwegian',
            'pl': 'Polish',
            'th': 'Thai',
            'tr': 'Turkish',
            'vi': 'Vietnamese',
            'ro': 'Romanian',
            'hu': 'Hungarian',
            'ms': 'Malay',
            'bg': 'Bulgarian',
            'tl': 'Tagalog',
            'sr': 'Serbian',
            'sk': 'Slovak',
            'uk': 'Ukrainian',
        },
        # Valid translations -- a mapping of source languages to the
        # translatable target languages.
        'translations': {
            'es': [
                'en'
            ],
            'en': [
                'el', 'en', 'zh', 'vi',
                'it', 'ar', 'cs', 'id',
                'es', 'ru', 'nl', 'pt',
                'no', 'tr', 'tl', 'th',
                'ro', 'pl', 'fr', 'bg',
                'uk', 'de', 'da', 'fi',
                'hu', 'ja', 'he', 'sr',
                'ko', 'sv', 'sk', 'ms'
            ],
        }
    }
}


def video_image_path(video_image_instance, filename):  # pylint:disable=unused-argument
    """
    Returns video image path.

    Arguments:
        video_image_instance (VideoImage): This is passed automatically by models.CustomizableImageField
        filename (str): name of image file
    """
    return u'{}{}'.format(settings.VIDEO_IMAGE_SETTINGS.get('DIRECTORY_PREFIX', ''), filename)


def get_video_image_storage():
    """
    Return the configured django storage backend.
    """
    if hasattr(settings, 'VIDEO_IMAGE_SETTINGS'):
        return get_storage_class(
            settings.VIDEO_IMAGE_SETTINGS.get('STORAGE_CLASS'),
        )(**settings.VIDEO_IMAGE_SETTINGS.get('STORAGE_KWARGS', {}))

    # during edx-platform loading this method gets called but settings are not ready yet
    # so in that case we will return default(FileSystemStorage) storage class instance
    return get_storage_class()()


def video_transcript_path(video_transcript_instance, filename):  # pylint:disable=unused-argument
    """
    Returns video transcript path.

    Arguments:
        video_transcript_instance (VideoTranscript): This is passed automatically by models.CustomizableFileField
        filename (str): name of image file
    """
    return u'{}{}'.format(settings.VIDEO_TRANSCRIPTS_SETTINGS.get('DIRECTORY_PREFIX', ''), filename)


def get_video_transcript_storage():
    """
    Return the configured django storage backend for video transcripts.
    """
    if hasattr(settings, 'VIDEO_TRANSCRIPTS_SETTINGS'):
        return get_storage_class(
            settings.VIDEO_TRANSCRIPTS_SETTINGS.get('STORAGE_CLASS'),
        )(**settings.VIDEO_TRANSCRIPTS_SETTINGS.get('STORAGE_KWARGS', {}))

    # during edx-platform loading this method gets called but settings are not ready yet
    # so in that case we will return default(FileSystemStorage) storage class instance
    return get_storage_class()()


def create_file_in_fs(file_data, file_name, file_system, static_dir):
    """
    Writes file in specific file system.

    Arguments:
        file_data (str): Data to store into the file.
        file_name (str): File name of the file to be created.
        file_system (OSFS): Import file system.
        static_dir (str): The Directory to retrieve transcript file.
    """
    with file_system.open(combine(static_dir, file_name), 'wb') as f:
        f.write(file_data.encode('utf-8'))


def get_transcript_format(transcript_content):
    """
    Returns transcript format.

    Arguments:
        transcript_content (str): Transcript file content.
    """
    try:
        json.loads(transcript_content)
    except ValueError:
        # With error handling (set to 'ERROR_RAISE'), we will be getting
        # the exception if something went wrong in parsing the transcript.

        srt_subs = SubRipFile.from_string(transcript_content, error_handling=SubRipFile.ERROR_RAISE)
        if srt_subs:
            return TranscriptFormat.SRT
    return TranscriptFormat.SJSON


def validate_generated_images(value, max_items):
    """
    Validate data before saving to database.

    Arguments:
        value(list): list to be validated
        max_items (int): maximum number of items in a list

    Returns:
        list if validation is successful

    Raises:
        ValidationError
    """
    if len(value) > max_items:
        raise ValidationError(
            u'list must not contain more than {max_items} items.'.format(max_items=max_items)
        )

    if all(isinstance(item, six.string_types) for item in value) is False:
        raise ValidationError(u'list must only contain strings.')

    return value


def invalidate_fernet_cached_properties(model, fields):
    """
    Invalidates transcript credential fernet field's cached properties.

    Arguments:
        model (class): Model class containing fernet fields.
        fields (list):  A list of fernet fields whose cache is to be invalidated.
    """
    for field_name in fields:
        try:
            field = model._meta.get_field(field_name)
            del field.keys
            del field.fernet_keys
            del field.fernet
        except AttributeError:
            pass


def validate_request_params(data, attributes):
    """
    Checks if the given set of attributes are missing from request and returns a response if true.

    Arguments:
        data(dict): params dict
        attributes(list): list of required attributes
    Returns:
        HTTP Response if params are missing,else None
    """
    missing = [attr for attr in attributes if attr not in data]
    if missing:
        return Response(
            status=status.HTTP_400_BAD_REQUEST,
            data={'message': '{missing} must be specified.'.format(missing=' and '.join(missing))}

        )
    return None
