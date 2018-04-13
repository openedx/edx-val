"""
Views file for django app edxval.
"""
import logging

from django.core.exceptions import ValidationError
from django.shortcuts import get_object_or_404
from rest_framework import generics, status
from rest_framework.authentication import SessionAuthentication
from rest_framework.permissions import DjangoModelPermissions
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_oauth.authentication import OAuth2Authentication

from edxval.api import create_or_update_video_transcript
from edxval.models import (
    CourseVideo,
    TranscriptProviderType,
    Video,
    VideoImage,
    VideoTranscript
)
from edxval.serializers import VideoSerializer
from edxval.utils import TranscriptFormat

LOGGER = logging.getLogger(__name__)  # pylint: disable=C0103

VALID_VIDEO_STATUSES = [
    'transcription_in_progress',
    'transcript_ready',
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


class MultipleFieldLookupMixin(object):
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
    authentication_classes = (OAuth2Authentication, SessionAuthentication)
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
    authentication_classes = (OAuth2Authentication, SessionAuthentication)
    permission_classes = (ReadRestrictedDjangoModelPermissions,)
    lookup_field = "edx_video_id"
    queryset = Video.objects.all()
    serializer_class = VideoSerializer


class VideoTranscriptView(APIView):
    """
    A Transcription View, used by edx-video-pipeline to create video transcripts.
    """
    authentication_classes = (OAuth2Authentication, SessionAuthentication)

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
            LOGGER.warn(
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
    authentication_classes = (OAuth2Authentication, SessionAuthentication)

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
    authentication_classes = (OAuth2Authentication, SessionAuthentication)

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
            course_video = CourseVideo.objects.select_related('video_image').get(
                course_id=unicode(course_id), video__edx_video_id=edx_video_id
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
