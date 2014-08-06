from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status, generics

from edxval.models import Video
from edxval.serializers import (
    VideoSerializer
)


class VideoList(generics.ListCreateAPIView):
    """
    GETs or POST video objects
    """
    queryset = Video.objects.all().select_related("encoded_videos")
    lookup_field = "edx_video_id"
    serializer_class = VideoSerializer


class VideoDetail(generics.RetrieveUpdateDestroyAPIView):
    """
    Gets a video instance given its edx_video_id
    """
    lookup_field = "edx_video_id"
    queryset = Video.objects.all()
    serializer_class = VideoSerializer
