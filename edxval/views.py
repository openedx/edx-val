"""
Views file for django app edxval.
"""
from __future__ import absolute_import

import logging

import six
from django.core.exceptions import ValidationError
from django.shortcuts import get_object_or_404
from edx_rest_framework_extensions.auth.jwt.authentication import JwtAuthentication
from rest_framework import generics, status
from rest_framework.authentication import SessionAuthentication
from rest_framework.permissions import DjangoModelPermissions
from rest_framework.response import Response
from rest_framework.views import APIView

from edxval.api import create_or_update_video_transcript
from edxval.enum import TranscriptionProviderErrorType
from edxval.models import (
    LIST_MAX_ITEMS,
    CourseVideo,
    EncodedVideo,
    Profile,
    TranscriptCredentials,
    TranscriptProviderType,
    Video,
    VideoImage,
    VideoTranscript,
)
from edxval.serializers import VideoSerializer
from edxval.transcript_utils import get_api_token
from edxval.utils import TranscriptFormat, validate_generated_images, validate_request_params

LOGGER = logging.getLogger(__name__)

VALID_VIDEO_STATUSES = [
    'transcription_in_progress',
    'transcript_ready',
    'transcode_active',
]


class ReadRestrictedDjangoModelPermissions(DjangoModelPermissions):
    """Extending DjangoModelPermissions to allow us to restrict read access.

    Django permissions typically only have add/change/delete. This class assumes
    that if you don't have permission to change it, you don't have permission to
    see it either. The only users of this REST API for the moment are those
    authorized to upload assets from video production.
    """
    perms_map = {
        'GET': ['%(app_label)s.change_%(model_name)s'],
        'OPTIONS': ['%(app_label)s.change_%(model_name)s'],
        'HEAD': ['%(app_label)s.change_%(model_name)s'],
        'POST': ['%(app_label)s.add_%(model_name)s'],
        'PUT': ['%(app_label)s.change_%(model_name)s'],
        'PATCH': ['%(app_label)s.change_%(model_name)s'],
        'DELETE': ['%(app_label)s.delete_%(model_name)s'],
    }


class MultipleFieldLookupMixin:
    """
    Apply this mixin to any view or viewset to get multiple field filtering
    based on a `lookup_fields` attribute, instead of the default single field filtering.
    """
    def get_object(self):
        """
        Returns an object instance that should be used for detail views.
        """
        queryset = self.get_queryset()             # Get the base queryset
        queryset = self.filter_queryset(queryset)  # Apply any filter backends
        filter = {}  # pylint: disable=W0622
        for field in self.lookup_fields:
            filter[field] = self.kwargs[field]
        return get_object_or_404(queryset, **filter)  # Lookup the object


class VideoList(generics.ListCreateAPIView):
    """
    GETs or POST video objects
    """
    authentication_classes = (JwtAuthentication, SessionAuthentication)
    permission_classes = (ReadRestrictedDjangoModelPermissions,)
    queryset = Video.objects.all().prefetch_related("encoded_videos", "courses")
    lookup_field = "edx_video_id"
    serializer_class = VideoSerializer

    def get_queryset(self):
        qset = Video.objects.all().prefetch_related("encoded_videos", "courses")

        args = self.request.GET
        course_id = args.get('course')
        if course_id:
            # view videos by course id
            qset = qset.filter(courses__course_id=course_id)
        youtube_id = args.get('youtube')
        if youtube_id:
            # view videos by youtube id
            qset = qset & Video.by_youtube_id(youtube_id)
        return qset


class VideoDetail(generics.RetrieveUpdateDestroyAPIView):
    """
    Gets a video instance given its edx_video_id
    """
    authentication_classes = (JwtAuthentication, SessionAuthentication)
    permission_classes = (ReadRestrictedDjangoModelPermissions,)
    lookup_field = "edx_video_id"
    queryset = Video.objects.all()
    serializer_class = VideoSerializer


class VideoTranscriptView(APIView):
    """
    A Transcription View, used by edx-video-pipeline to create video transcripts.
    """
    authentication_classes = (JwtAuthentication, SessionAuthentication)

    # noinspection PyMethodMayBeStatic
    def post(self, request):
        """
        Creates a video transcript instance with the given information.

        Arguments:
            request: A WSGI request.
        """
        attrs = ('video_id', 'name', 'language_code', 'provider', 'file_format')
        missing = [attr for attr in attrs if attr not in request.data]
        if missing:
            LOGGER.warning(
                '[VAL] Required transcript params are missing. %s', ' and '.join(missing)
            )
            return Response(
                status=status.HTTP_400_BAD_REQUEST,
                data=dict(message=u'{missing} must be specified.'.format(missing=' and '.join(missing)))
            )

        video_id = request.data['video_id']
        language_code = request.data['language_code']
        transcript_name = request.data['name']
        provider = request.data['provider']
        file_format = request.data['file_format']

        supported_formats = sorted(dict(TranscriptFormat.CHOICES).keys())
        if file_format not in supported_formats:
            message = (
                u'"{format}" transcript file type is not supported. Supported formats are "{supported_formats}"'
            ).format(format=file_format, supported_formats=supported_formats)
            return Response(status=status.HTTP_400_BAD_REQUEST, data={'message': message})

        supported_providers = sorted(dict(TranscriptProviderType.CHOICES).keys())
        if provider not in supported_providers:
            message = (
                u'"{provider}" provider is not supported. Supported transcription providers are "{supported_providers}"'
            ).format(provider=provider, supported_providers=supported_providers)
            return Response(status=status.HTTP_400_BAD_REQUEST, data={'message': message})

        transcript = VideoTranscript.get_or_none(video_id, language_code)
        if transcript is None:
            create_or_update_video_transcript(video_id, language_code, metadata={
                'provider': provider,
                'file_name': transcript_name,
                'file_format': file_format
            })
            response = Response(status=status.HTTP_200_OK)
        else:
            message = (
                u'Can not override existing transcript for video "{video_id}" and language code "{language}".'
            ).format(video_id=video_id, language=language_code)
            response = Response(status=status.HTTP_400_BAD_REQUEST, data={'message': message})

        return response


class VideoStatusView(APIView):
    """
    A Video View to update the status of a video.

    Note:
        Currently, the valid statuses are `transcription_in_progress` and `transcript_ready` because it
        was intended to only be used for video transcriptions but if you found it helpful to your needs, you
        can add more statuses so that you can use it for updating other video statuses too.
    """
    authentication_classes = (JwtAuthentication, SessionAuthentication)

    def patch(self, request):
        """
        Update the status of a video.
        """
        attrs = ('edx_video_id', 'status')
        missing = [attr for attr in attrs if attr not in request.data]
        if missing:
            return Response(
                status=status.HTTP_400_BAD_REQUEST,
                data={'message': u'"{missing}" params must be specified.'.format(missing=' and '.join(missing))}
            )

        edx_video_id = request.data['edx_video_id']
        video_status = request.data['status']
        if video_status not in VALID_VIDEO_STATUSES:
            return Response(
                status=status.HTTP_400_BAD_REQUEST,
                data={'message': u'"{status}" is not a valid Video status.'.format(status=video_status)}
            )

        try:
            video = Video.objects.get(edx_video_id=edx_video_id)
            video.status = video_status
            video.save()
            response_status = status.HTTP_200_OK
            response_payload = {}
        except Video.DoesNotExist:
            response_status = status.HTTP_400_BAD_REQUEST
            response_payload = {
                'message': u'Video is not found for specified edx_video_id: {edx_video_id}'.format(
                    edx_video_id=edx_video_id
                )
            }

        return Response(status=response_status, data=response_payload)


class VideoImagesView(APIView):
    """
    View to update course video images.
    """
    authentication_classes = (JwtAuthentication, SessionAuthentication)

    def post(self, request):
        """
        Update a course video image instance with auto generated image names.
        """
        attrs = ('course_id', 'edx_video_id', 'generated_images')
        missing = [attr for attr in attrs if attr not in request.data]
        if missing:
            return Response(
                status=status.HTTP_400_BAD_REQUEST,
                data={
                    'message': u'{missing} must be specified to update a video image.'.format(
                        missing=' and '.join(missing)
                    )
                }
            )

        course_id = request.data['course_id']
        edx_video_id = request.data['edx_video_id']
        generated_images = request.data['generated_images']

        try:
            validate_generated_images(generated_images, LIST_MAX_ITEMS)
        except Exception as e:  # pylint: disable=broad-except
            return Response(
                status=status.HTTP_400_BAD_REQUEST,
                data={'message': str(e)}
            )

        try:
            course_video = CourseVideo.objects.select_related('video_image').get(
                course_id=six.text_type(course_id), video__edx_video_id=edx_video_id
            )
        except CourseVideo.DoesNotExist:
            return Response(
                status=status.HTTP_400_BAD_REQUEST,
                data={'message': u'CourseVideo not found for course_id: {course_id}'.format(course_id=course_id)}
            )

        try:
            VideoImage.create_or_update(course_video, generated_images=generated_images)
        except ValidationError as ex:
            return Response(
                status=status.HTTP_400_BAD_REQUEST,
                data={'message': str(ex)}
            )

        return Response()


class HLSMissingVideoView(APIView):
    """
    A View to list video ids which are missing HLS encodes and update an encode profile for a video.
    """
    authentication_classes = (JwtAuthentication, SessionAuthentication)

    def post(self, request):
        """
        Retrieve video IDs that are missing HLS profiles. This endpoint supports 2 types of input data:

        1. If we want a batch of video ids which are missing HLS profile irrespective of their courses, the request
           data should be in following format:
                {
                    'batch_size': 50,
                    'offset': 0
                }
           And response will be in following format:
                {
                    'videos': ['video_id1', 'video_id2', 'video_id3', ... , video_id50],
                    'total': 300,
                    'offset': 50,
                    'batch_size': 50
                }

        2. If we want all the videos which are missing HLS profiles in a set of specific courses, the request data
           should be in following format:
                {
                    'courses': [
                        'course_id1',
                        'course_id2',
                        ...
                    ]
                }
           And response will be in following format:
                {
                    'videos': ['video_id1', 'video_id2', 'video_id3', ...]
                }
        """
        courses = request.data.get('courses')
        batch_size = request.data.get('batch_size', 50)
        offset = request.data.get('offset', 0)
        if courses:
            videos = (CourseVideo.objects.select_related('video')
                      .prefetch_related('video__encoded_videos', 'video__encoded_videos__profile')
                      .filter(course_id__in=courses, video__status='file_complete')
                      .exclude(video__encoded_videos__profile__profile_name='hls')
                      .values_list('video__edx_video_id', flat=True)
                      .distinct())

            response = Response({'videos': videos}, status=status.HTTP_200_OK)
        else:
            videos = (Video.objects.prefetch_related('encoded_videos', 'encoded_videos__profile')
                      .filter(status='file_complete')
                      .exclude(encoded_videos__profile__profile_name='hls')
                      .order_by('id')
                      .values_list('edx_video_id', flat=True)
                      .distinct())

            response = Response(
                {
                    'videos': videos[offset: offset + batch_size],
                    'total': videos.count(),
                    'offset': offset,
                    'batch_size': batch_size,
                },
                status=status.HTTP_200_OK
            )

        return response

    def put(self, request):
        """
        Update a single profile for a given video.

        Example request data:
            {
                'edx_video_id': '1234'
                'profile': 'hls',
                'encode_data': {
                    'url': 'foo.com/qwe.m3u8'
                    'file_size': 34
                    'bitrate': 12
                }
            }
        """
        edx_video_id = request.data['edx_video_id']
        profile = request.data['profile']
        encode_data = request.data['encode_data']

        video = Video.objects.get(edx_video_id=edx_video_id)
        profile = Profile.objects.get(profile_name=profile)

        # Delete existing similar profile if its present and
        # create new one with updated data.
        EncodedVideo.objects.filter(video=video, profile=profile).delete()
        EncodedVideo.objects.create(video=video, profile=profile, **encode_data)

        return Response(status=status.HTTP_200_OK)


class TranscriptCredentialsView(APIView):
    """
    API View to fetch and create Transcript provider credentials.
    """
    authentication_classes = (JwtAuthentication, SessionAuthentication)
    permission_classes = (ReadRestrictedDjangoModelPermissions,)
    queryset = TranscriptCredentials.objects.all()

    def get(self, request):
        """
        Retrieves the transcript credentials for a given organization and provider.

        **Example requests**:

            GET api/val/v0/videos/transcript-credentials/?
            provider=3play
            &org=org

        **GET Parameters**:

            The following query parameters are required to get the credentials:

                * provider(str): transcript provider, which is either 3PlayMedia or Cielo24.

                * org(str): organization whose credentials are to be fetch.

        **Response Values**

            For a successful request, the following values are returned along with 200 status:

                * api_key(str): provider key

                * api_secret_key(str): provider api secret key(only for 3PlayMedia)

                * provider(str): transcript provider

                * org(str): organization whose credentials are fetched.

            For the error, 400 response code is returned with:

                * message(str): error message
        """
        response = validate_request_params(request.query_params, ['org', 'provider'])
        if response:
            return response

        org = request.query_params['org']
        provider = request.query_params['provider']
        try:
            credentials = TranscriptCredentials.objects.get(
                provider=provider, org=org
            )
            status_code = status.HTTP_200_OK
            data = dict(
                api_key=credentials.api_key,
                api_secret_key=credentials.api_secret,
                org=credentials.org,
                provider=credentials.provider
            )
        except TranscriptCredentials.DoesNotExist:
            status_code = status.HTTP_400_BAD_REQUEST
            data = {'message': "Credentials not found for provider {provider} & organization {org}".format(
                provider=provider,
                org=org
            )}

        return Response(status=status_code, data=data)

    def validate_missing_attributes(self, provider, attributes, credentials):
        """
        Returns error message if provided attributes are not presents in credentials.
        """
        error_message = None
        missing = [attr for attr in attributes if attr not in credentials]
        if missing:
            error_message = '{missing} must be specified for {provider}.'.format(
                provider=provider,
                missing=' and '.join(missing)
            )

        return TranscriptionProviderErrorType.MISSING_REQUIRED_ATTRIBUTES, error_message

    def validate_transcript_credentials(self, provider, **credentials):
        """
        Validates transcript credentials.

        Validations:
            Providers must be either 3PlayMedia or Cielo24.
            In case of:
                3PlayMedia - 'api_key' and 'api_secret_key' are required.
                Cielo24 - Valid 'api_key' and 'username' are required.
        """
        error_type, error_message, validated_credentials = None, '', {}
        if provider in [TranscriptProviderType.CIELO24, TranscriptProviderType.THREE_PLAY_MEDIA]:
            if provider == TranscriptProviderType.CIELO24:
                must_have_props = ('org', 'api_key', 'username')
                error_type, error_message = self.validate_missing_attributes(provider, must_have_props, credentials)

                if not error_message:
                    # Get cielo api token and store it in api_key.
                    api_token = get_api_token(credentials['username'], credentials['api_key'])
                    if api_token:
                        validated_credentials.update({
                            'org': credentials['org'],
                            'api_key': api_token
                        })
                    else:
                        error_message = 'Invalid credentials supplied.'
                        error_type = TranscriptionProviderErrorType.INVALID_CREDENTIALS
            else:
                must_have_props = ('org', 'api_key', 'api_secret_key')
                error_type, error_message = self.validate_missing_attributes(provider, must_have_props, credentials)
                if not error_message:
                    validated_credentials.update({
                        'org': credentials['org'],
                        'api_key': credentials['api_key'],
                        'api_secret': credentials['api_secret_key']
                    })
        else:
            error_message = 'Invalid provider {provider}.'.format(provider=provider)
            error_type = TranscriptionProviderErrorType.INVALID_PROVIDER

        return error_type, error_message, validated_credentials

    def post(self, request):
        """
        Creates or updates the org-specific transcript credentials with the given information.

        Arguments:
            request: A WSGI request.

        **Example Request**

            POST api/val/v0/videos/transcript-credentials/ {
                "provider": "3PlayMedia",
                "org": "test.x",
                "api_key": "test-api-key",
                "api_secret_key": "test-api-secret-key"
            }

        **POST Parameters**

            A POST request can include the following parameters.

            * provider: A string representation of provider.

            * org: A string representing the organizaton code.

            * api_key: A string representing the provider api key.

            * api_secret_key: (Required for 3Play only). A string representing the api secret key.

            * username: (Required for Cielo only). A string representing the cielo username.

            **Example POST Response**

            In case of success:
                Returns an empty response with 201 status code (HTTP 201 Created).

            In case of error:
                Return response with error message and 400 status code (HTTP 400 Bad Request).
                {
                    "error_type": INVALID_CREDENTIALS
                    "message": "Error message."
                }
        """
        # Validate credentials
        provider = request.data.pop('provider', None)
        error_type, error_message, validated_credentials = self.validate_transcript_credentials(
            provider=provider, **request.data
        )
        if error_message:
            return Response(
                status=status.HTTP_400_BAD_REQUEST,
                data=dict(error_type=error_type, message=error_message)
            )

        TranscriptCredentials.objects.update_or_create(
            org=validated_credentials.pop('org'), provider=provider, defaults=validated_credentials
        )

        return Response(status=status.HTTP_201_CREATED)
