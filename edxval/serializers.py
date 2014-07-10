"""
Serializers for Video Abstraction Layer
"""
from rest_framework import serializers
from django.core.validators import MinValueValidator

from edxval.models import Profile


class VideoSerializer(serializers.Serializer):
    edx_video_id = serializers.CharField(required=True, max_length=50)
    duration = serializers.FloatField()
    client_title = serializers.CharField(max_length=255)


class ProfileSerializer(serializers.ModelSerializer):
    class Meta:
        model = Profile
        fields = (
            "profile_name",
            "extension",
            "width",
            "height"
        )


class OnlyEncodedVideoSerializer(serializers.Serializer):
    """
    Used to serialize the EncodedVideo fir the EncodedVideoSetSerializer
    """
    url = serializers.URLField(max_length=200)
    file_size = serializers.IntegerField(validators=[MinValueValidator(1)])
    bitrate = serializers.IntegerField(validators=[MinValueValidator(1)])
    profile = ProfileSerializer()


class EncodedVideoSetSerializer(serializers.Serializer):
    """
    Used to serialize a list of EncodedVideo objects it's foreign key Video Object.
    """
    edx_video_id = serializers.CharField(max_length=50)
    client_title = serializers.CharField(max_length=255)
    duration = serializers.FloatField(validators=[MinValueValidator(1)])
    encoded_videos = OnlyEncodedVideoSerializer()
