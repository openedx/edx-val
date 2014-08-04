"""
Serializers for Video Abstraction Layer
"""
from rest_framework import serializers

from edxval.models import Profile, Video, EncodedVideo


class VideoSerializer(serializers.ModelSerializer):

    def restore_object(self, attrs, instance=None):
        """
        Given a dictionary of deserialized field values, either update
        an existing model instance, or create a new model instance.
        """
        if instance is not None:
            instance.edx_video_id = attrs.get(
                'edx_video_id', instance.edx_video_id
            )
            instance.duration = attrs.get(
                'duration', instance.duration
            )
            instance.client_video_id = attrs.get(
                'client_video_id', instance.client_video_id
            )
            return instance
        return Video(**attrs)

    class Meta:
        model = Video
        fields = (
            "client_video_id",
            "duration",
            "edx_video_id"
        )

class ProfileSerializer(serializers.ModelSerializer):
    class Meta:
        model = Profile
        fields = (
            "profile_name",
            "extension",
            "width",
            "height"
        )


class OnlyEncodedVideoSerializer(serializers.ModelSerializer):
    """
    Used to serialize the EncodedVideo for the EncodedVideoSetSerializer
    """
    profile = ProfileSerializer(required=False)
    class Meta:
        model = EncodedVideo
        fields = (
            "url",
            "file_size",
            "bitrate"
        )


class EncodedVideoSetSerializer(serializers.ModelSerializer):
    """
    Used to serialize a list of EncodedVideo objects it's foreign key Video Object.
    """
    edx_video_id = serializers.CharField(max_length=50)
    encoded_videos = OnlyEncodedVideoSerializer()

    class Meta:
        model = Video
        fields = (
            "duration",
            "client_video_id"
        )

