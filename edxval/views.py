"""
Views file for django app edxval.
"""

from rest_framework import generics
from rest_framework.permissions import DjangoModelPermissionsOrAnonReadOnly
from django.http import HttpResponse
from django.shortcuts import get_object_or_404
from django.views.decorators.http import last_modified

from edxval.models import Video, Profile, Subtitle
from edxval.serializers import (
    VideoSerializer,
    ProfileSerializer,
    SubtitleSerializer
)

class MultipleFieldLookupMixin(object):
    """
    Apply this mixin to any view or viewset to get multiple field filtering
    based on a `lookup_fields` attribute, instead of the default single field filtering.
    """
    def get_object(self):
        queryset = self.get_queryset()             # Get the base queryset
        queryset = self.filter_queryset(queryset)  # Apply any filter backends
        filter = {}
        for field in self.lookup_fields:
            filter[field] = self.kwargs[field]
        return get_object_or_404(queryset, **filter)  # Lookup the object


class VideoList(generics.ListCreateAPIView):
    """
    GETs or POST video objects
    """
    permission_classes = (DjangoModelPermissionsOrAnonReadOnly,)
    queryset = Video.objects.all().prefetch_related("encoded_videos")
    lookup_field = "edx_video_id"
    serializer_class = VideoSerializer


class ProfileList(generics.ListCreateAPIView):
    """
    GETs or POST video objects
    """
    permission_classes = (DjangoModelPermissionsOrAnonReadOnly,)
    queryset = Profile.objects.all()
    lookup_field = "profile_name"
    serializer_class = ProfileSerializer


class VideoDetail(generics.RetrieveUpdateDestroyAPIView):
    """
    Gets a video instance given its edx_video_id
    """
    permission_classes = (DjangoModelPermissionsOrAnonReadOnly,)
    lookup_field = "edx_video_id"
    queryset = Video.objects.all()
    serializer_class = VideoSerializer


class SubtitleDetail(MultipleFieldLookupMixin, generics.RetrieveUpdateDestroyAPIView):
    """
    Gets a subtitle instance given its id
    """
    permission_classes = (DjangoModelPermissionsOrAnonReadOnly,)
    lookup_fields = ("video__edx_video_id", "language")
    queryset = Subtitle.objects.all()
    serializer_class = SubtitleSerializer


def _last_modified_subtitle(request, edx_video_id, language):
    return Subtitle.objects.get(video__edx_video_id=edx_video_id, language=language).modified

@last_modified(last_modified_func=_last_modified_subtitle)
def get_subtitle(request, edx_video_id, language):
    """
    Return content of subtitle by id
    """
    sub = Subtitle.objects.get(video__edx_video_id=edx_video_id, language=language)
    response = HttpResponse(sub.content, content_type=sub.content_type)
    return response
