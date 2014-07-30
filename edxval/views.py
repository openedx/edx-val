
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status, generics

from edxval.models import Video
from edxval.serializers import VideoSerializer


class VideoList(APIView):
    """
    HTTP API for Video objects
    """

    def get(self, request, format=None):
        """
        Gets all videos
        """
        video = Video.objects.all()
        serializer = VideoSerializer(video, many=True)
        return Response(serializer.data)

    def post(self, request, format=None):
        """
        Takes an object (where we get our list of dict) and creates the objects

        Request.DATA is a list of dictionaries. Each item is individually validated
        and if valid, saved. All invalid dicts are returned in the error message.

        Args:
            request (object): Object where we get our information for POST
            format (str): format of our data (JSON, XML, etc.)

        Returns:
            Response(message, HTTP status)

        """
        if not isinstance(request.DATA, list):
            error_message = "Not a list: {0}".format(type(request.DATA))
            return Response(error_message, status=status.HTTP_400_BAD_REQUEST)
        invalid_videos = []
        for item in request.DATA:
            try:
                instance = Video.objects.get(
                    edx_video_id=item.get("edx_video_id")
                )
            except Video.DoesNotExist:
                instance = None
            serializer = VideoSerializer(instance, data=item)
            if serializer.is_valid():
                serializer.save()
            else:
                invalid_videos.append((serializer.errors, item))
        if invalid_videos:
            return Response(invalid_videos, status=status.HTTP_400_BAD_REQUEST)
        else:
            return Response(status=status.HTTP_201_CREATED)


class VideoDetail(generics.RetrieveUpdateDestroyAPIView):
    """
    Gets a video instance given its edx_video_id
    """
    lookup_field = "edx_video_id"
    queryset = Video.objects.all()
    serializer_class = VideoSerializer
