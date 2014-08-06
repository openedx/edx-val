from rest_framework import generics

from edxval.models import Video
from edxval.serializers import (
    VideoSerializer
)


class VideoList(generics.ListCreateAPIView):
    """
    GETs or POST video objects
    """
    queryset = Video.objects.all().prefetch_related("encoded_videos")
    lookup_field = "edx_video_id"
    serializer_class = VideoSerializer


class VideoDetail(generics.RetrieveUpdateDestroyAPIView):
    """
    Gets a video instance given its edx_video_id
    """
    lookup_field = "edx_video_id"
    queryset = Video.objects.all()
    serializer_class = VideoSerializer
