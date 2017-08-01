"""
Views file for django app edxval.
"""
from rest_framework.views import APIView
from rest_framework import generics
from rest_framework.authentication import SessionAuthentication
from rest_framework_oauth.authentication import OAuth2Authentication
from rest_framework.permissions import DjangoModelPermissions
from rest_framework.response import Response
from rest_framework import status
from django.http import HttpResponse
from django.shortcuts import get_object_or_404
from django.core.exceptions import ValidationError
from django.views.decorators.http import last_modified

from edxval.api import get_video_transcript, update_video_transcript, create_video_transcript
from edxval.models import Video, Profile, Transcript, CourseVideo, VideoImage, TranscriptFormat, TranscriptProviderType
from edxval.serializers import (
    VideoSerializer,
    TranscriptSerializer,
)


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
    A Transcription View, used by VEDA to create video transcripts.
    """
    authentication_classes = (OAuth2Authentication, SessionAuthentication)

    # noinspection PyMethodMayBeStatic
    def post(self, request):
        """
        Creates a video transcript instance with the given information.

        Arguments:
            request: A WSGI request.
        """
        attrs = ('video_id', 'language', 'url', 'format', 'provider')
        missing = [attr for attr in attrs if attr not in request.data]
        if missing:
            return Response(
                status=status.HTTP_400_BAD_REQUEST,
                data=dict(message=u'{missing} must be specified.'.format(missing=' and '.join(missing)))
            )

        video_id = request.data['video_id']
        language = request.data['language']
        transcript_url = request.data['url']
        transcript_format = request.data['format']
        provider = request.data['provider']

        supported_formats = dict(TranscriptFormat.CHOICES).keys()
        if transcript_format not in supported_formats:
            return Response(
                status=status.HTTP_400_BAD_REQUEST,
                data=dict(
                    message=(u'This transcript file type is not supported. Supported formats are'
                             u'{supported_formats}').format(supported_formats=supported_formats)
                )
            )

        supported_providers = dict(TranscriptProviderType.CHOICES).keys()
        if provider not in supported_providers:
            return Response(
                status=status.HTTP_400_BAD_REQUEST,
                data=dict(
                    message=(u'This provider is not supported. Supported transcription providers are'
                             u'{supported_providers}').format(supported_providers=supported_providers)
                )
            )

        transcript = get_video_transcript(video_id, language)
        if not transcript:
            serialized_transcript = create_video_transcript(
                video_id=video_id,
                language=language,
                transcript_url=transcript_url,
                transcript_format=transcript_format,
            )
            response = Response(data=serialized_transcript, status=status.HTTP_200_OK)
        else:
            response = Response(
                data=dict(
                    message=(u'Transcript for video "{video_id}" and lang code "{language}" already exists. '
                             u'It can not be overwritten.').format(video_id=video_id, language=language)
                ),
                status=status.HTTP_400_BAD_REQUEST
            )

        return response


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
