"""
Views file for django app edxval.
"""
from rest_framework import generics
from rest_framework.authentication import SessionAuthentication
from rest_framework_oauth.authentication import OAuth2Authentication
from rest_framework.permissions import DjangoModelPermissions
from django.http import HttpResponse
from django.shortcuts import get_object_or_404
from django.views.decorators.http import last_modified

from edxval.models import Video, Profile, Subtitle
from edxval.serializers import (
    VideoSerializer,
    SubtitleSerializer
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


class SubtitleDetail(MultipleFieldLookupMixin, generics.RetrieveUpdateDestroyAPIView):
    """
    Gets a subtitle instance given its id
    """
    authentication_classes = (OAuth2Authentication, SessionAuthentication)
    permission_classes = (ReadRestrictedDjangoModelPermissions,)
    lookup_fields = ("video__edx_video_id", "language")
    queryset = Subtitle.objects.all()
    serializer_class = SubtitleSerializer


def _last_modified_subtitle(request, edx_video_id, language):  # pylint: disable=W0613
    """
    Returns the last modified subtitle
    """
    return Subtitle.objects.get(video__edx_video_id=edx_video_id, language=language).modified

@last_modified(last_modified_func=_last_modified_subtitle)
def get_subtitle(request, edx_video_id, language): # pylint: disable=W0613
    """
    Return content of subtitle by id
    """
    sub = Subtitle.objects.get(video__edx_video_id=edx_video_id, language=language)
    response = HttpResponse(sub.content, content_type=sub.content_type)
    return response
