"""
Views file for django app edxval.
"""

from rest_framework import generics
from django.http import HttpResponse
from django.views.decorators.http import last_modified

from edxval.models import Video, Profile, Subtitle
from edxval.serializers import (
    VideoSerializer,
    ProfileSerializer,
    SubtitleSerializer
)


class VideoList(generics.ListCreateAPIView):
    """
    GETs or POST video objects
    """
    queryset = Video.objects.all().prefetch_related("encoded_videos")
    lookup_field = "edx_video_id"
    serializer_class = VideoSerializer


class ProfileList(generics.ListCreateAPIView):
    """
    GETs or POST video objects
    """
    queryset = Profile.objects.all()
    lookup_field = "profile_name"
    serializer_class = ProfileSerializer


class VideoDetail(generics.RetrieveUpdateDestroyAPIView):
    """
    Gets a video instance given its edx_video_id
    """
    lookup_field = "edx_video_id"
    queryset = Video.objects.all()
    serializer_class = VideoSerializer


class SubtitleDetail(generics.RetrieveUpdateDestroyAPIView):
    """
    Gets a subtitle instance given its id
    """
    lookup_field = "id"
    queryset = Subtitle.objects.all()
    serializer_class = SubtitleSerializer


@last_modified(last_modified_func=lambda request, subtitle_id: Subtitle.objects.get(pk=subtitle_id).modified)
def get_subtitle(request, subtitle_id):
    """
    Return content of subtitle by id
    """
    sub = Subtitle.objects.get(pk=subtitle_id)
    response = HttpResponse(sub.content, content_type=sub.content_type)
    return response
