"""
Views file for django app edxval.
"""

from rest_framework import generics

from edxval.models import Video, Profile
from edxval.serializers import (
    VideoSerializer,
    ProfileSerializer
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
