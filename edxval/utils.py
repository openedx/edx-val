"""
Util methods to be used in api and models.
"""
import hashlib
import json
from contextlib import closing

from django.conf import settings
from django.core.exceptions import ValidationError
from django.utils.module_loading import import_string

from fs.path import combine
from pysrt import SubRipFile


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
    return '{}{}'.format(settings.VIDEO_IMAGE_SETTINGS.get('DIRECTORY_PREFIX', ''), filename)


def get_video_image_storage():
    """
    Return the configured django storage backend.
    """
    return get_storage_from_settings('VIDEO_IMAGE_SETTINGS')


def video_transcript_path(video_transcript_instance, filename):  # pylint:disable=unused-argument
    """
    Returns video transcript path.

    Arguments:
        video_transcript_instance (VideoTranscript): This is passed automatically by models.CustomizableFileField
        filename (str): name of image file
    """
    return '{}{}'.format(settings.VIDEO_TRANSCRIPTS_SETTINGS.get('DIRECTORY_PREFIX', ''), filename)


def get_video_transcript_storage():
    """
    Return the configured django storage backend for video transcripts.
    """
    return get_storage_from_settings('VIDEO_TRANSCRIPTS_SETTINGS')


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
            f'list must not contain more than {max_items} items.'
        )

    if all(isinstance(item, str) for item in value) is False:
        raise ValidationError('list must only contain strings.')

    return value


def generate_file_content_hash(uploaded_file):
    """
    Generates SHA256 Content Hash for a File

    Arguments:
        uploaded_file (UploadedFile): File which will be used for hash generation

    Returns:
        str sha256 hash
    """
    with closing(uploaded_file.open()) as file_data:
        file_content = file_data.read()
        if isinstance(file_content, str):
            file_content = file_content.encode('utf-8')

    content_hash = hashlib.sha256(file_content)

    return content_hash.hexdigest()


def is_duplicate_file(uploaded_file_1, uploaded_file_2):
    """
    Checks two files to know if they are duplicates by checking content hash

    Arguments:
        uploaded_file_1 (UploadedFile): File which will be compared to the second file
        uploaded_file_2 (UploadedFile): File which will be compared to the first file

    Returns:
        if file is duplicate (boolean)
    """
    uploaded_file_1_hash = generate_file_content_hash(uploaded_file_1)
    uploaded_file_2_hash = generate_file_content_hash(uploaded_file_2)

    return uploaded_file_1_hash == uploaded_file_2_hash


def get_storage_from_settings(storage_name):
    """
    Returns a Django storage instance based on a nested settings dictionary.

    Args:
        storage_name (str): The attribute name on `settings` that contains the storage config dict.

    Returns:
        An instance of the configured storage class.
    """
    config = getattr(settings, storage_name, {})

    storage_class_path = config.get('STORAGE_CLASS')
    options = config.get('STORAGE_KWARGS', {})

    if not storage_class_path:
        storage_class_path = getattr(
            settings, 'DEFAULT_FILE_STORAGE', 'django.core.files.storage.FileSystemStorage'
        )

    storage_class = import_string(storage_class_path)
    return storage_class(**options)
