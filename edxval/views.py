
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status, generics

from edxval.models import Video
from edxval.serializers import VideoSerializer, EncodedVideoSetDeserializer, EncodedVideoSetSerializer




class VideoList(APIView):
    """
<<<<<<< HEAD
    HTTP API for Video and EncodedVideo objects
    """

    def get(self, request, format=None):
        """
        Gets all videos
        """
        video = Video.objects.all()
        serializer = EncodedVideoSetSerializer(video, many=True)
        return Response(serializer.data)

    def post(self, request, format=None):
        """
        Takes a Video dict of a list of EncodedVideo dicts and creates the objects

        Args:
            request (object): Object where we get our information for POST
            data_format (str): format of our data (JSON, XML, etc.)

        Returns:
            Response(message, HTTP status)

        """
        serializer = EncodedVideoSetDeserializer(data=request.DATA)
        if serializer.is_valid():
            serializer.save()
            return Response("Success", status=status.HTTP_201_CREATED)
        else:
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class VideoDetail(generics.RetrieveUpdateDestroyAPIView):
    """
    Gets a video instance given its edx_video_id
    """
    lookup_field = "edx_video_id"
    queryset = Video.objects.all()
    serializer_class = VideoSerializer
