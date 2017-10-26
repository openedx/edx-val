# pylint: disable=E1101
# -*- coding: utf-8 -*-
"""
The internal API for VAL.
"""
import logging
from enum import Enum

from django.core.exceptions import ObjectDoesNotExist, ValidationError
from lxml import etree
from lxml.etree import Element, SubElement

from edxval.exceptions import (InvalidTranscriptFormat,
                               InvalidTranscriptProvider, ValCannotCreateError,
                               ValCannotUpdateError, ValInternalError,
                               ValVideoNotFoundError)
from edxval.models import (CourseVideo, EncodedVideo, Profile,
                           TranscriptFormat, TranscriptPreference,
                           TranscriptProviderType, Video, VideoImage,
                           VideoTranscript, ThirdPartyTranscriptCredentialsState)
from edxval.serializers import TranscriptPreferenceSerializer, TranscriptSerializer, VideoSerializer
from edxval.utils import THIRD_PARTY_TRANSCRIPTION_PLANS

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
    filter_attrs = {'video_id': video_id}
    if language_code:
        filter_attrs['language_code'] = language_code

    transcript_set = VideoTranscript.objects.filter(**filter_attrs)
    return transcript_set.exists()


def get_video_transcripts(video_id):
    """
    Get a video's transcripts

    Arguments:
        video_id: it can be an edx_video_id or an external_id extracted from external sources in a video component.
    """
    transcripts_set = VideoTranscript.objects.filter(video_id=video_id)

    transcripts = []
    if transcripts_set.exists():
        transcripts = TranscriptSerializer(transcripts_set, many=True).data

    return transcripts


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


def get_video_transcript_data(video_ids, language_code):
    """
    Get video transcript data

    Arguments:
        video_ids(list): list containing edx_video_id and external video ids extracted from
        external sources from a video component.
        language_code(unicode): it will be the language code of the requested transcript.

    Returns:
        A dict containing transcript file name and its content. It will be for a video whose transcript
        found first while iterating the video ids.
    """
    transcript_data = None
    for video_id in video_ids:
        try:
            video_transcript = VideoTranscript.objects.get(video_id=video_id, language_code=language_code)
            transcript_data = dict(
                file_name=video_transcript.transcript.name,
                content=video_transcript.transcript.file.read()
            )
            break
        except VideoTranscript.DoesNotExist:
            continue
        except Exception:
            logger.exception(
                '[edx-val] Error while retrieving transcript for video=%s -- language_code=%s',
                video_id,
                language_code
            )
            raise

    return transcript_data


def get_available_transcript_languages(video_ids):
    """
    Get available transcript languages

    Arguments:
        video_ids(list): list containing edx_video_id and external video ids extracted from
        external sources of a video component.

    Returns:
        A list containing unique transcript language codes for the video ids.
    """
    available_languages = VideoTranscript.objects.filter(
        video_id__in=video_ids
    ).values_list(
        'language_code', flat=True
    )
    return list(set(available_languages))


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


def create_or_update_video_transcript(
        video_id,
        language_code,
        file_name,
        file_format,
        provider,
        file_data=None,
    ):
    """
    Create or Update video transcript for an existing video.

    Arguments:
        video_id: it can be an edx_video_id or an external_id extracted from external sources in a video component.
        language_code: language code of a video transcript
        file_name: file name of a video transcript
        file_data (InMemoryUploadedFile): Transcript data to be saved for a course video.
        file_format: format of the transcript
        provider: transcript provider

    Returns:
        video transcript url
    """
    if file_format not in dict(TranscriptFormat.CHOICES).keys():
        raise InvalidTranscriptFormat('{} transcript format is not supported'.format(file_format))

    if provider not in dict(TranscriptProviderType.CHOICES).keys():
        raise InvalidTranscriptProvider('{} transcript provider is not supported'.format(provider))

    video_transcript, __ = VideoTranscript.create_or_update(
        video_id,
        language_code,
        file_name,
        file_format,
        provider,
        file_data,
    )

    return video_transcript.url()


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


def export_to_xml(video_ids, course_id=None, external=False):
    """
    Exports data for a video into an xml object.

    NOTE: For external video ids, only transcripts information will be added into xml.
          If external=False, then edx_video_id is going to be on first index of the list.

    Arguments:
        video_ids (list): It can contain edx_video_id and/or multiple external video ids.
                          We are passing all video ids associated with a video component
                          so that we can export transcripts for each video id.
        course_id (str): The ID of the course with which this video is associated
        external (bool): True if first video id in `video_ids` is not edx_video_id else False

    Returns:
        An lxml video_asset element containing export data

    Raises:
        ValVideoNotFoundError: if the video does not exist
    """
    # val does not store external videos, so construct transcripts information only.
    if external:
        video_el = Element('video_asset')
        return create_transcripts_xml(video_ids, video_el)

    # for an internal video, first video id must be edx_video_id
    video_id = video_ids[0]

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

    return create_transcripts_xml(video_ids, video_el)


def create_transcripts_xml(video_ids, video_el):
    """
    Create xml for transcripts.

    Arguments:
        video_ids (list): It can contain edx_video_id and/or multiple external video ids
        video_el (Element): lxml Element object

    Returns:
        lxml Element object with transcripts information
    """
    video_transcripts = VideoTranscript.objects.filter(video_id__in=video_ids)
    # create transcripts node only when we have transcripts for a video
    if video_transcripts.exists():
        transcripts_el = SubElement(video_el, 'transcripts')

    exported_language_codes = []
    for video_transcript in video_transcripts:
        if video_transcript.language_code not in exported_language_codes:
            SubElement(
                transcripts_el,
                'transcript',
                {
                    'video_id': video_transcript.video_id,
                    'file_name': video_transcript.transcript.name,
                    'language_code': video_transcript.language_code,
                    'file_format': video_transcript.file_format,
                    'provider': video_transcript.provider,
                }
            )
            exported_language_codes.append(video_transcript.language_code)

    return video_el


def import_from_xml(xml, edx_video_id, course_id=None):
    """
    Imports data from a video_asset element about the given video_id.

    If the edx_video_id already exists, then no changes are made. If an unknown
    profile is referenced by an encoded video, that encoding will be ignored.

    Arguments:
        xml (Element): An lxml video_asset element containing import data
        edx_video_id (str): val video id
        course_id (str): The ID of a course to associate the video with

    Raises:
        ValCannotCreateError: if there is an error importing the video
    """
    if xml.tag != 'video_asset':
        raise ValCannotCreateError('Invalid XML')

    # if edx_video_id does not exist then create video transcripts only
    if not edx_video_id:
        return create_transcript_objects(xml)

    # If video with edx_video_id already exists, associate it with the given course_id.
    try:
        video = Video.objects.get(edx_video_id=edx_video_id)
        logger.info(
            "edx_video_id '%s' present in course '%s' not imported because it exists in VAL.",
            edx_video_id,
            course_id,
        )
        if course_id:
            course_video, __ = CourseVideo.get_or_create_with_validation(video=video, course_id=course_id)

            image_file_name = xml.get('image', '').strip()
            if image_file_name:
                VideoImage.create_or_update(course_video, image_file_name)

        # import transcripts
        create_transcript_objects(xml)

        return
    except ValidationError as err:
        logger.exception(err.message)
        raise ValCannotCreateError(err.message_dict)
    except Video.DoesNotExist:
        pass

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
    create_video(data)
    create_transcript_objects(xml)


def create_transcript_objects(xml):
    """
    Create VideoTranscript objects.

    Arguments:
        xml (Element): lxml Element object
    """
    for transcript in xml.findall('.//transcripts/transcript'):
        try:
            VideoTranscript.create_or_update(
                transcript.attrib['video_id'],
                transcript.attrib['language_code'],
                transcript.attrib['file_name'],
                transcript.attrib['file_format'],
                transcript.attrib['provider'],
            )
        except KeyError:
            logger.warn("VAL: Required attributes are missing from xml, xml=[%s]", etree.tostring(transcript).strip())
