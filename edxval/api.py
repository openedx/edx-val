# pylint: disable=E1101
# -*- coding: utf-8 -*-
"""
The internal API for VAL.
"""
import logging
from enum import Enum
from uuid import uuid4

from django.core.exceptions import ObjectDoesNotExist, ValidationError
from django.core.files.base import ContentFile
from fs import open_fs
from fs.errors import ResourceNotFound
from fs.path import combine
from lxml import etree
from lxml.etree import Element, SubElement
from pysrt.srtexc import Error

from edxval.exceptions import (
    InvalidTranscriptFormat,
    TranscriptsGenerationException,
    InvalidTranscriptProvider,
    ValCannotCreateError,
    ValCannotUpdateError,
    ValInternalError,
    ValVideoNotFoundError,
)
from edxval.models import (
    CourseVideo,
    EncodedVideo,
    Profile,
    TranscriptPreference,
    TranscriptProviderType,
    Video,
    VideoImage,
    VideoTranscript,
    EXTERNAL_VIDEO_STATUS,
    ThirdPartyTranscriptCredentialsState,
)
from edxval.serializers import TranscriptPreferenceSerializer, TranscriptSerializer, VideoSerializer
from edxval.utils import (
    TranscriptFormat,
    THIRD_PARTY_TRANSCRIPTION_PLANS,
    create_file_in_fs,
    get_transcript_format,
)

from edxval.transcript_utils import Transcript


logger = logging.getLogger(__name__)  # pylint: disable=C0103


class VideoSortField(Enum):
    """An enum representing sortable fields in the Video model"""
    created = "created"
    edx_video_id = "edx_video_id"
    client_video_id = "client_video_id"
    duration = "duration"
    # status omitted because user-facing strings do not match data


class SortDirection(Enum):
    """An enum representing sort direction"""
    asc = "asc"
    desc = "desc"


def generate_video_id():
    """
    Generates a video ID.
    """
    return unicode(uuid4())


def create_video(video_data):
    """
    Called on to create Video objects in the database

    create_video is used to create Video objects whose children are EncodedVideo
    objects which are linked to Profile objects. This is an alternative to the HTTP
    requests so it can be used internally. The VideoSerializer is used to
    deserialize this object. If there are duplicate profile_names, the entire
    creation will be rejected. If the profile is not found in the database, the
    video will not be created.
    Args:
        video_data (dict):
         {
                url: api url to the video
                edx_video_id: ID of the video
                duration: Length of video in seconds
                client_video_id: client ID of video
                encoded_video: a list of EncodedVideo dicts
                    url: url of the video
                    file_size: size of the video in bytes
                    profile: ID of the profile
                courses: Courses associated with this video
                image: poster image file name for a particular course
         }

    Raises:
        Raises ValCannotCreateError if the video cannot be created.

    Returns the successfully created Video object
    """

    serializer = VideoSerializer(data=video_data)
    if serializer.is_valid():
        serializer.save()
        return video_data.get("edx_video_id")
    else:
        raise ValCannotCreateError(serializer.errors)


def create_external_video(display_name):
    """
    Create an external video.

    Arguments:
        display_name(unicode): Client title for the external video
    """
    return create_video({
        'edx_video_id': generate_video_id(),
        'status': EXTERNAL_VIDEO_STATUS,
        'client_video_id': display_name,
        'duration': 0,
        'encoded_videos': [],
        'courses': []
    })


def update_video(video_data):
    """
    Called on to update Video objects in the database

    update_video is used to update Video objects by the given edx_video_id in the video_data.

    Args:
        video_data (dict):
         {
                url: api url to the video
                edx_video_id: ID of the video
                duration: Length of video in seconds
                client_video_id: client ID of video
                encoded_video: a list of EncodedVideo dicts
                    url: url of the video
                    file_size: size of the video in bytes
                    profile: ID of the profile
                courses: Courses associated with this video
         }

    Raises:
        Raises ValVideoNotFoundError if the video cannot be retrieved.
        Raises ValCannotUpdateError if the video cannot be updated.

    Returns the successfully updated Video object
    """

    try:
        video = _get_video(video_data.get("edx_video_id"))
    except Video.DoesNotExist:
        error_message = u"Video not found when trying to update video with edx_video_id: {0}".format(video_data.get("edx_video_id"))
        raise ValVideoNotFoundError(error_message)

    serializer = VideoSerializer(video, data=video_data)
    if serializer.is_valid():
        serializer.save()
        return video_data.get("edx_video_id")
    else:
        raise ValCannotUpdateError(serializer.errors)


def update_video_status(edx_video_id, status):
    """
    Update status for an existing video.

    Args:
        edx_video_id: ID of the video
        status: video status

    Raises:
        Raises ValVideoNotFoundError if the video cannot be retrieved.
    """

    try:
        video = _get_video(edx_video_id)
    except Video.DoesNotExist:
        error_message = u"Video not found when trying to update video status with edx_video_id: {0}".format(
            edx_video_id
        )
        raise ValVideoNotFoundError(error_message)

    video.status = status
    video.save()


def is_video_available(edx_video_id):
    """
    Returns whether a video exists given a video ID.

    Arguments:
     edx_video_id: A video ID representing a video record in db.
    """
    return Video.objects.filter(edx_video_id=edx_video_id).exists()


def get_transcript_credentials_state_for_org(org, provider=None):
    """
    Returns transcript credentials state for an org

    Arguments:
        org (unicode): course organization
        provider (unicode): transcript provider

    Returns:
        dict: provider name and their credential existance map

        {
            u'Cielo24': True
        }
        {
            u'3PlayMedia': False,
            u'Cielo24': True
        }
    """
    query_filter = {'org': org}
    if provider:
        query_filter['provider'] = provider

    return {
        credential.provider: credential.exists
        for credential in ThirdPartyTranscriptCredentialsState.objects.filter(**query_filter)
    }


def update_transcript_credentials_state_for_org(org, provider, exists):
    """
    Updates transcript credentials state for a course organization.

    Arguments:
        org (unicode): course organization
        provider (unicode): transcript provider
        exists (bool): state of credentials
    """
    ThirdPartyTranscriptCredentialsState.update_or_create(org, provider, exists)


def is_transcript_available(video_id, language_code=None):
    """
    Returns whether the transcripts are available for a video.

    Arguments:
        video_id: it can be an edx_video_id or an external_id extracted from external sources in a video component.
        language_code: it will the language code of the requested transcript.
    """
    filter_attrs = {'video__edx_video_id': video_id}
    if language_code:
        filter_attrs['language_code'] = language_code

    transcript_set = VideoTranscript.objects.filter(**filter_attrs)
    return transcript_set.exists()


def get_video_transcript(video_id, language_code):
    """
    Get video transcript info

    Arguments:
        video_id(unicode): A video id, it can be an edx_video_id or an external video id extracted from
        external sources of a video component.
        language_code(unicode): it will be the language code of the requested transcript.
    """
    transcript = VideoTranscript.get_or_none(video_id=video_id, language_code=language_code)
    return TranscriptSerializer(transcript).data if transcript else None


def get_video_transcript_data(video_id, language_code):
    """
    Get video transcript data

    Arguments:
        video_id(unicode): An id identifying the Video.
        language_code(unicode): it will be the language code of the requested transcript.

    Returns:
        A dict containing transcript file name and its content.
    """
    video_transcript = VideoTranscript.get_or_none(video_id, language_code)
    if video_transcript:
        try:
            return dict(file_name=video_transcript.filename, content=video_transcript.transcript.file.read())
        except Exception:
            logger.exception(
                '[edx-val] Error while retrieving transcript for video=%s -- language_code=%s',
                video_id,
                language_code
            )
            raise


def get_available_transcript_languages(video_id):
    """
    Get available transcript languages

    Arguments:
        video_id(unicode): An id identifying the Video.

    Returns:
        A list containing transcript language codes for the Video.
    """
    available_languages = VideoTranscript.objects.filter(
        video__edx_video_id=video_id
    ).values_list(
        'language_code', flat=True
    )
    return list(available_languages)


def get_video_transcript_url(video_id, language_code):
    """
    Returns course video transcript url or None if no transcript

    Arguments:
        video_id: it can be an edx_video_id or an external_id extracted from external sources in a video component.
        language_code: language code of a video transcript
    """
    video_transcript = VideoTranscript.get_or_none(video_id, language_code)
    if video_transcript:
        return video_transcript.url()


def create_video_transcript(video_id, language_code, file_format, content, provider=TranscriptProviderType.CUSTOM):
    """
    Create a video transcript.

    Arguments:
        video_id(unicode): An Id identifying the Video data model object.
        language_code(unicode): A language code.
        file_format(unicode): Transcript file format.
        content(InMemoryUploadedFile): Transcript content.
        provider(unicode): Transcript provider (it will be 'custom' by default if not selected).
    """
    transcript_serializer = TranscriptSerializer(
        data=dict(provider=provider, language_code=language_code, file_format=file_format),
        context=dict(video_id=video_id),
    )
    if transcript_serializer.is_valid():
        transcript_serializer.save(content=content)
        return transcript_serializer.data
    else:
        raise ValCannotCreateError(transcript_serializer.errors)


def create_or_update_video_transcript(video_id, language_code, metadata, file_data=None):
    """
    Create or Update video transcript for an existing video.

    Arguments:
        video_id: it can be an edx_video_id or an external_id extracted from external sources in a video component.
        language_code: language code of a video transcript
        metadata (dict): A dict containing (to be overwritten) properties
        file_data (InMemoryUploadedFile): Transcript data to be saved for a course video.

    Returns:
        video transcript url
    """
    # Filter wanted properties
    metadata = {
        prop: value
        for prop, value in metadata.iteritems()
        if prop in ['provider', 'language_code', 'file_name', 'file_format'] and value
    }

    file_format = metadata.get('file_format')
    if file_format and file_format not in dict(TranscriptFormat.CHOICES).keys():
        raise InvalidTranscriptFormat('{} transcript format is not supported'.format(file_format))

    provider = metadata.get('provider')
    if provider and provider not in dict(TranscriptProviderType.CHOICES).keys():
        raise InvalidTranscriptProvider('{} transcript provider is not supported'.format(provider))

    try:
        # Video should be present in edxval in order to attach transcripts to it.
        video = Video.objects.get(edx_video_id=video_id)
        video_transcript, __ = VideoTranscript.create_or_update(video, language_code, metadata, file_data)
    except Video.DoesNotExist:
        return None

    return video_transcript.url()


def delete_video_transcript(video_id, language_code):
    """
    Delete transcript for an existing video.

    Arguments:
        video_id: id identifying the video to which the transcript is associated.
        language_code: language code of a video transcript.
    """
    video_transcript = VideoTranscript.get_or_none(video_id, language_code)
    if video_transcript:
        # delete the transcript content from storage.
        video_transcript.transcript.delete()
        # delete the transcript metadata from db.
        video_transcript.delete()
        logger.info('Transcript is removed for video "%s" and language code "%s"', video_id, language_code)


def get_3rd_party_transcription_plans():
    """
    Retrieves 3rd party transcription plans.
    """
    return THIRD_PARTY_TRANSCRIPTION_PLANS


def get_transcript_preferences(course_id):
    """
    Retrieves course wide transcript preferences

    Arguments:
        course_id (str): course id
    """
    try:
        transcript_preference = TranscriptPreference.objects.get(course_id=course_id)
    except TranscriptPreference.DoesNotExist:
        return

    return TranscriptPreferenceSerializer(transcript_preference).data


def create_or_update_transcript_preferences(course_id, **preferences):
    """
    Creates or updates course-wide transcript preferences

    Arguments:
        course_id(str): course id

    Keyword Arguments:
        preferences(dict): keyword arguments
    """
    transcript_preference, __ = TranscriptPreference.objects.update_or_create(
        course_id=course_id, defaults=preferences
    )
    return TranscriptPreferenceSerializer(transcript_preference).data


def remove_transcript_preferences(course_id):
    """
    Deletes course-wide transcript preferences.

    Arguments:
        course_id(str): course id
    """
    try:
        transcript_preference = TranscriptPreference.objects.get(course_id=course_id)
        transcript_preference.delete()
    except TranscriptPreference.DoesNotExist:
        pass


def get_course_video_image_url(course_id, edx_video_id):
    """
    Returns course video image url or None if no image found
    """
    try:
        video_image = CourseVideo.objects.select_related('video_image').get(
            course_id=course_id, video__edx_video_id=edx_video_id
        ).video_image
        return video_image.image_url()
    except ObjectDoesNotExist:
        return None


def update_video_image(edx_video_id, course_id, image_data, file_name):
    """
    Update video image for an existing video.

    NOTE: If `image_data` is None then `file_name` value will be used as it is, otherwise
    a new file name is constructed based on uuid and extension from `file_name` value.
    `image_data` will be None in case of course re-run and export.

    Arguments:
        image_data (InMemoryUploadedFile): Image data to be saved for a course video.

    Returns:
        course video image url

    Raises:
        Raises ValVideoNotFoundError if the CourseVideo cannot be retrieved.
    """
    try:
        course_video = CourseVideo.objects.select_related('video').get(
            course_id=course_id, video__edx_video_id=edx_video_id
        )
    except ObjectDoesNotExist:
        error_message = u'VAL: CourseVideo not found for edx_video_id: {0} and course_id: {1}'.format(
            edx_video_id,
            course_id
        )
        raise ValVideoNotFoundError(error_message)

    video_image, _ = VideoImage.create_or_update(course_video, file_name, image_data)
    return video_image.image_url()


def create_profile(profile_name):
    """
    Used to create Profile objects in the database

    A profile needs to exists before an EncodedVideo object can be created.

    Args:
        profile_name (str): ID of the profile

    Raises:
        ValCannotCreateError: Raised if the profile name is invalid or exists
    """
    try:
        profile = Profile(profile_name=profile_name)
        profile.full_clean()
        profile.save()
    except ValidationError as err:
        raise ValCannotCreateError(err.message_dict)


def _get_video(edx_video_id):
    """
    Get a Video instance, prefetching encoded video and course information.

    Raises ValVideoNotFoundError if the video cannot be retrieved.
    """
    try:
        return Video.objects.prefetch_related("encoded_videos", "courses").get(edx_video_id=edx_video_id)
    except Video.DoesNotExist:
        error_message = u"Video not found for edx_video_id: {0}".format(edx_video_id)
        raise ValVideoNotFoundError(error_message)
    except Exception:
        error_message = u"Could not get edx_video_id: {0}".format(edx_video_id)
        logger.exception(error_message)
        raise ValInternalError(error_message)


def get_video_info(edx_video_id):
    """
    Retrieves all encoded videos of a video found with given video edx_video_id

    Args:
        edx_video_id (str): id for video content.

    Returns:
        (dict): Deserialized Video Object with related field EncodedVideo
            Returns all the Video object fields, and it's related EncodedVideo
            objects in a list.
            {
                url: api url to the video
                edx_video_id: ID of the video
                status: Status of the video as a string
                duration: Length of video in seconds
                client_video_id: client ID of video
                encoded_video: a list of EncodedVideo dicts
                    url: url of the video
                    file_size: size of the video in bytes
                    profile: ID of the profile
            }

    Raises:
        ValVideoNotFoundError: Raised if video doesn't exist
        ValInternalError: Raised for unknown errors

    Example:
        Given one EncodedVideo with edx_video_id "example"
        >>> get_video_info("example")
        Returns (dict):
        {
            'url' : '/edxval/videos/example',
            'edx_video_id': u'example',
            'duration': 111.0,
            'client_video_id': u'The example video',
            'encoded_videos': [
                {
                    'url': u'http://www.example.com',
                    'file_size': 25556,
                    'bitrate': 9600,
                    'profile': u'mobile'
                 }
            ]
        }
    """
    return VideoSerializer(_get_video(edx_video_id)).data


def get_urls_for_profiles(edx_video_id, profiles):
    """
    Returns a dict mapping profiles to URLs.

    If the profiles or video is not found, urls will be blank.

    Args:
        edx_video_id (str): id of the video
        profiles (list): list of profiles we want to search for

    Returns:
        (dict): A dict containing the profile to url pair
    """
    profiles_to_urls = {profile: None for profile in profiles}
    try:
        video_info = get_video_info(edx_video_id)
    except ValVideoNotFoundError:
        return profiles_to_urls

    for encoded_video in video_info["encoded_videos"]:
        if encoded_video["profile"] in profiles:
            profiles_to_urls[encoded_video["profile"]] = encoded_video["url"]

    return profiles_to_urls


def get_url_for_profile(edx_video_id, profile):
    """
    Uses get_urls_for_profile to obtain a single profile

    Args:
        edx_video_id (str): id of the video
        profile (str): a string of the profile we are searching

    Returns:
        (str): A string with the url

    """
    return get_urls_for_profiles(edx_video_id, [profile])[profile]


def _get_videos_for_filter(video_filter, sort_field=None, sort_dir=SortDirection.asc):
    """
    Returns a generator expression that contains the videos found, sorted by
    the given field and direction, with ties broken by edx_video_id to ensure a
    total order.
    """
    videos = Video.objects.filter(**video_filter)
    if sort_field:
        # Refining by edx_video_id ensures a total order
        videos = videos.order_by(sort_field.value, "edx_video_id")
        if sort_dir == SortDirection.desc:
            videos = videos.reverse()
    return (VideoSerializer(video).data for video in videos)


def get_course_video_ids_with_youtube_profile(course_ids=None, offset=None, limit=None):
    """
    Returns a list that contains all the course ids and video ids with the youtube profile

    Args:
         course_ids (list): valid course ids
         limit (int): batch records limit
         offset (int): an offset for selecting a batch
    Returns:
         (list): Tuples of course_id, edx_video_id and youtube video url
    """
    course_videos = (CourseVideo.objects.select_related('video')
                     .prefetch_related('video__encoded_videos', 'video__encoded_videos__profile')
                     .filter(video__encoded_videos__profile__profile_name='youtube')
                     .order_by('id')
                     .distinct())

    if course_ids:
        course_videos = course_videos.filter(course_id__in=course_ids)

    course_videos = course_videos.values_list('course_id', 'video__edx_video_id')
    if limit is not None and offset is not None:
        course_videos = course_videos[offset: offset+limit]

    course_videos_with_yt_profile = []
    for course_id, edx_video_id in course_videos:
        yt_profile = EncodedVideo.objects.filter(
            video__edx_video_id=edx_video_id,
            profile__profile_name='youtube'
        ).first()

        if yt_profile:
            course_videos_with_yt_profile.append((
                course_id, edx_video_id, yt_profile.url
            ))

    return course_videos_with_yt_profile


def get_videos_for_course(course_id, sort_field=None, sort_dir=SortDirection.asc):
    """
    Returns an iterator of videos for the given course id.

    Args:
        course_id (String)
        sort_field (VideoSortField)
        sort_dir (SortDirection)

    Returns:
        A generator expression that contains the videos found, sorted by the
        given field and direction, with ties broken by edx_video_id to ensure a
        total order.
    """
    return _get_videos_for_filter(
        {'courses__course_id': unicode(course_id), 'courses__is_hidden': False},
        sort_field,
        sort_dir,
    )


def remove_video_for_course(course_id, edx_video_id):
    """
    Soft deletes video for particular course.

    Arguments:
        course_id (str): id of the course
        edx_video_id (str): id of the video to be hidden
    """
    course_video = CourseVideo.objects.get(course_id=course_id, video__edx_video_id=edx_video_id)
    course_video.is_hidden = True
    course_video.save()


def get_videos_for_ids(
        edx_video_ids,
        sort_field=None,
        sort_dir=SortDirection.asc
):
    """
    Returns an iterator of videos that match the given list of ids.

    Args:
        edx_video_ids (list)
        sort_field (VideoSortField)
        sort_dir (SortDirection)

    Returns:
        A generator expression that contains the videos found, sorted by the
        given field and direction, with ties broken by edx_video_id to ensure a
        total order
    """
    return _get_videos_for_filter(
        {"edx_video_id__in":edx_video_ids},
        sort_field,
        sort_dir,
    )


def get_video_info_for_course_and_profiles(course_id, profiles):
    """
    Returns a dict of edx_video_ids with a dict of requested profiles.

    Args:
        course_id (str): id of the course
        profiles (list): list of profile_names
    Returns:
        (dict): Returns all the profiles attached to a specific
        edx_video_id
        {
            edx_video_id: {
                'duration': length of the video in seconds,
                'profiles': {
                    profile_name: {
                        'url': url of the encoding
                        'file_size': size of the file in bytes
                    },
                }
            },
        }
    Example:
        Given two videos with two profiles each in course_id 'test_course':
        {
            u'edx_video_id_1': {
                u'duration: 1111,
                u'profiles': {
                    u'mobile': {
                        'url': u'http: //www.example.com/meow',
                        'file_size': 2222
                    },
                    u'desktop': {
                        'url': u'http: //www.example.com/woof',
                        'file_size': 4444
                    }
                }
            },
            u'edx_video_id_2': {
                u'duration: 2222,
                u'profiles': {
                    u'mobile': {
                        'url': u'http: //www.example.com/roar',
                        'file_size': 6666
                    },
                    u'desktop': {
                        'url': u'http: //www.example.com/bzzz',
                        'file_size': 8888
                    }
                }
            }
        }
    """
    # In case someone passes in a key (VAL doesn't really understand opaque keys)
    course_id = unicode(course_id)
    try:
        encoded_videos = EncodedVideo.objects.filter(
            profile__profile_name__in=profiles,
            video__courses__course_id=course_id
        ).select_related()
    except Exception:
        error_message = u"Could not get encoded videos for course: {0}".format(course_id)
        logger.exception(error_message)
        raise ValInternalError(error_message)

    # DRF serializers were causing extra queries for some reason...
    return_dict = {}
    for enc_vid in encoded_videos:
        # Add duration to edx_video_id
        return_dict.setdefault(enc_vid.video.edx_video_id, {}).update(
            {
                "duration": enc_vid.video.duration,
            }
        )
        # Add profile information to edx_video_id's profiles
        return_dict[enc_vid.video.edx_video_id].setdefault("profiles", {}).update(
            {enc_vid.profile.profile_name: {
                "url": enc_vid.url,
                "file_size": enc_vid.file_size,
            }}
        )
    return return_dict


def copy_course_videos(source_course_id, destination_course_id):
    """
    Adds the destination_course_id to the videos taken from the source_course_id

    Args:
        source_course_id: The original course_id
        destination_course_id: The new course_id where the videos will be copied
    """
    if source_course_id == destination_course_id:
        return

    course_videos = CourseVideo.objects.select_related('video', 'video_image').filter(
        course_id=unicode(source_course_id)
    )

    for course_video in course_videos:
        destination_course_video, __ = CourseVideo.objects.get_or_create(
            video=course_video.video,
            course_id=destination_course_id
        )
        if hasattr(course_video, 'video_image'):
            VideoImage.create_or_update(
                course_video=destination_course_video,
                file_name=course_video.video_image.image.name
            )


def export_to_xml(video_id, resource_fs, static_dir, course_id=None):
    """
    Exports data for a video into an xml object.

    NOTE: For external video ids, only transcripts information will be added into xml.
          If external=False, then edx_video_id is going to be on first index of the list.

    Arguments:
        video_id (str): Video id of the video to export transcripts.
        course_id (str): The ID of the course with which this video is associated.
        static_dir (str): The Directory to store transcript file.
        resource_fs (SubFS): Export file system.

    Returns:
        An lxml video_asset element containing export data

    Raises:
        ValVideoNotFoundError: if the video does not exist
    """
    video_image_name = ''
    video = _get_video(video_id)

    try:
        course_video = CourseVideo.objects.select_related('video_image').get(course_id=course_id, video=video)
        video_image_name = course_video.video_image.image.name
    except ObjectDoesNotExist:
        pass

    video_el = Element(
        'video_asset',
        attrib={
            'client_video_id': video.client_video_id,
            'duration': unicode(video.duration),
            'image': video_image_name
        }
    )
    for encoded_video in video.encoded_videos.all():
        SubElement(
            video_el,
            'encoded_video',
            {
                name: unicode(getattr(encoded_video, name))
                for name in ['profile', 'url', 'file_size', 'bitrate']
            }
        )

    return create_transcripts_xml(video_id, video_el, resource_fs, static_dir)


def create_transcript_file(video_id, language_code, file_format, resource_fs, static_dir):
    """
    Writes transcript file to file system.

    Arguments:
        video_id (str): Video id of the video transcript file is attached.
        language_code (str): Language code of the transcript.
        file_format (str): File format of the transcript file.
        static_dir (str): The Directory to store transcript file.
        resource_fs (SubFS): The file system to store transcripts.
    """
    transcript_filename = '{video_id}-{language_code}.srt'.format(
        video_id=video_id,
        language_code=language_code
    )
    transcript_data = get_video_transcript_data(video_id, language_code)
    if transcript_data:
        transcript_content = Transcript.convert(
            transcript_data['content'],
            input_format=file_format,
            output_format=Transcript.SRT
        )
        create_file_in_fs(transcript_content, transcript_filename, resource_fs, static_dir)

    return transcript_filename


def create_transcripts_xml(video_id, video_el, resource_fs, static_dir):
    """
    Creates xml for transcripts.
    For each transcript element, an associated transcript file is also created in course OLX.

    Arguments:
        video_id (str): Video id of the video.
        video_el (Element): lxml Element object
        static_dir (str): The Directory to store transcript file.
        resource_fs (SubFS): The file system to store transcripts.

    Returns:
        lxml Element object with transcripts information
    """
    video_transcripts = VideoTranscript.objects.filter(video__edx_video_id=video_id).order_by('language_code')
    # create transcripts node only when we have transcripts for a video
    if video_transcripts.exists():
        transcripts_el = SubElement(video_el, 'transcripts')

    transcript_files_map = {}
    for video_transcript in video_transcripts:
        language_code = video_transcript.language_code
        file_format = video_transcript.file_format

        try:
            transcript_filename = create_transcript_file(
                video_id=video_id,
                language_code=language_code,
                file_format=file_format,
                resource_fs=resource_fs.delegate_fs(),
                static_dir=combine(u'course', static_dir)  # File system should not start from /draft directory.
            )
            transcript_files_map[language_code] = transcript_filename
        except TranscriptsGenerationException:
            # we don't want to halt export in this case, just log and move to the next transcript.
            logger.exception('[VAL] Error while generating "%s" transcript for video["%s"].', language_code, video_id)
            continue

        SubElement(
            transcripts_el,
            'transcript',
            {
                'language_code': language_code,
                'file_format': Transcript.SRT,
                'provider': video_transcript.provider,
            }
        )

    return dict(xml=video_el, transcripts=transcript_files_map)


def import_from_xml(xml, edx_video_id, resource_fs, static_dir, external_transcripts=dict(), course_id=None):
    """
    Imports data from a video_asset element about the given video_id.

    If the edx_video_id already exists, then no changes are made. If an unknown
    profile is referenced by an encoded video, that encoding will be ignored.

    Arguments:
        xml (Element): An lxml video_asset element containing import data
        edx_video_id (str): val video id
        resource_fs (OSFS): Import file system.
        static_dir (str): The Directory to retrieve transcript file.
        external_transcripts (dict): A dict containing the list of names of the external transcripts.
            Example:
            {
                'en': ['The_Flash.srt', 'Harry_Potter.srt'],
                'es': ['Green_Arrow.srt']
            }
        course_id (str): The ID of a course to associate the video with

    Raises:
        ValCannotCreateError: if there is an error importing the video

    Returns:
        edx_video_id (str): val video id.
    """
    if xml.tag != 'video_asset':
        raise ValCannotCreateError('Invalid XML')

    # If video with edx_video_id already exists, associate it with the given course_id.
    try:
        if not edx_video_id:
            raise Video.DoesNotExist

        video = Video.objects.get(edx_video_id=edx_video_id)
        logger.info(
            "edx_video_id '%s' present in course '%s' not imported because it exists in VAL.",
            edx_video_id,
            course_id,
        )

        # We don't want to link an existing video to course if its an external video.
        # External videos do not have any playback profiles associated, these are just to track video
        # transcripts for those video components who do not use edx hosted videos for playback.
        if course_id and video.status != EXTERNAL_VIDEO_STATUS:
            course_video, __ = CourseVideo.get_or_create_with_validation(video=video, course_id=course_id)

            image_file_name = xml.get('image', '').strip()
            if image_file_name:
                VideoImage.create_or_update(course_video, image_file_name)

        return edx_video_id
    except ValidationError as err:
        logger.exception(err.message)
        raise ValCannotCreateError(err.message_dict)
    except Video.DoesNotExist:
        pass

    if edx_video_id:
        # Video with edx_video_id did not exist, so create one from xml data.
        data = {
            'edx_video_id': edx_video_id,
            'client_video_id': xml.get('client_video_id'),
            'duration': xml.get('duration'),
            'status': 'imported',
            'encoded_videos': [],
            'courses': [{course_id: xml.get('image')}] if course_id else [],
        }
        for encoded_video_el in xml.iterfind('encoded_video'):
            profile_name = encoded_video_el.get('profile')
            try:
                Profile.objects.get(profile_name=profile_name)
            except Profile.DoesNotExist:
                logger.info(
                    "Imported edx_video_id '%s' contains unknown profile '%s'.",
                    edx_video_id,
                    profile_name
                )
                continue
            data['encoded_videos'].append({
                'profile': profile_name,
                'url': encoded_video_el.get('url'),
                'file_size': encoded_video_el.get('file_size'),
                'bitrate': encoded_video_el.get('bitrate'),
            })

        if not data['encoded_videos']:
            # Video's status does not get included in video xml at the time of export. So, at this point,
            # we cannot tell from xml that whether a video had an external status. But if encoded videos
            # are not set, the chances are, the video was an external one, in which case, we will not link
            # it to the course(s). Even if the video wasn't an external one and it is having 0 encodes in
            # xml, it does not have a side effect if not linked to a course, since the video was already
            # non-playable.
            data['status'] = EXTERNAL_VIDEO_STATUS
            data['courses'] = []

        # Create external video if no edx_video_id.
        edx_video_id = create_video(data)
    else:
        edx_video_id = create_external_video('External Video')

    create_transcript_objects(xml, edx_video_id, resource_fs, static_dir, external_transcripts)
    return edx_video_id


def import_transcript_from_fs(edx_video_id, language_code, file_name, provider, resource_fs, static_dir):
    """
    Imports transcript file from file system and creates transcript record in DS.

    Arguments:
        edx_video_id (str): Video id of the video.
        language_code (unicode): Language code of the requested transcript.
        file_name (unicode): File name of the transcript file.
        provider (unicode): Transcript provider.
        resource_fs (OSFS): Import file system.
        static_dir (str): The Directory to retrieve transcript file.
    """
    file_format = None
    transcript_data = get_video_transcript_data(edx_video_id, language_code)

    # First check if transcript record does not exist.
    if not transcript_data:
        # Read file from import file system and attach it to transcript record in DS.
        try:
            with resource_fs.open(combine(static_dir, file_name), 'rb') as f:
                file_content = f.read()
                file_content = file_content.decode('utf-8-sig')
        except ResourceNotFound as exc:
            # Don't raise exception in case transcript file is not found in course OLX.
            logger.warn(
                '[edx-val] "%s" transcript "%s" for video "%s" is not found.',
                language_code,
                file_name,
                edx_video_id
            )
            return
        except UnicodeDecodeError:
            # Don't raise exception in case transcript contains non-utf8 content.
            logger.warn(
                '[edx-val] "%s" transcript "%s" for video "%s" contains a non-utf8 file content.',
                language_code,
                file_name,
                edx_video_id
            )
            return

        # Get file format from transcript content.
        try:
            file_format = get_transcript_format(file_content)
        except Error as ex:
            # Don't raise exception, just don't create transcript record.
            logger.warn(
                '[edx-val] Error while getting transcript format for video=%s -- language_code=%s --file_name=%s',
                edx_video_id,
                language_code,
                file_name
            )
            return

        # Create transcript record.
        create_video_transcript(
            video_id=edx_video_id,
            language_code=language_code,
            file_format=file_format,
            content=ContentFile(file_content),
            provider=provider
        )


def create_transcript_objects(xml, edx_video_id, resource_fs, static_dir, external_transcripts):
    """
    Create VideoTranscript objects.

    Arguments:
        xml (Element): lxml Element object.
        edx_video_id (str): Video id of the video.
        resource_fs (OSFS): Import file system.
        static_dir (str): The Directory to retrieve transcript file.
        external_transcripts (dict): A dict containing the list of names of the external transcripts.
            Example:
            {
                'en': ['The_Flash.srt', 'Harry_Potter.srt'],
                'es': ['Green_Arrow.srt']
            }
    """
    # File system should not start from /draft directory.
    with open_fs(resource_fs.root_path.split('/drafts')[0]) as file_system:
        # First import VAL transcripts.
        for transcript in xml.findall('.//transcripts/transcript'):
            try:
                file_format = transcript.attrib['file_format']
                language_code = transcript.attrib['language_code']
                transcript_file_name = u'{edx_video_id}-{language_code}.{file_format}'.format(
                    edx_video_id=edx_video_id,
                    language_code=language_code,
                    file_format=file_format
                )

                import_transcript_from_fs(
                    edx_video_id=edx_video_id,
                    language_code=transcript.attrib['language_code'],
                    file_name=transcript_file_name,
                    provider=transcript.attrib['provider'],
                    resource_fs=file_system,
                    static_dir=static_dir
                )
            except KeyError:
                logger.warn("VAL: Required attributes are missing from xml, xml=[%s]", etree.tostring(transcript).strip())

        # This won't overwrite transcript for a language which is already present for the video.
        for language_code, transcript_file_names in external_transcripts.iteritems():
            for transcript_file_name in transcript_file_names:
                import_transcript_from_fs(
                    edx_video_id=edx_video_id,
                    language_code=language_code,
                    file_name=transcript_file_name,
                    provider=TranscriptProviderType.CUSTOM,
                    resource_fs=file_system,
                    static_dir=static_dir
                )
