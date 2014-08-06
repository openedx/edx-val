"""
Serializers for Video Abstraction Layer
"""
from rest_framework import serializers

from edxval.models import Profile, Video, EncodedVideo


class ProfileSerializer(serializers.ModelSerializer):
    class Meta:
        model = Profile
        fields = (
            "profile_name",
            "extension",
            "width",
            "height"
        )


class EncodedVideoSerializer(serializers.ModelSerializer):
    profile = serializers.SlugRelatedField(slug_field="profile_name")

    class Meta:
        model = EncodedVideo
        fields = (
            "created",
            "modified",
            "url",
            "file_size",
            "bitrate",
            "profile",
        )


class VideoSerializer(serializers.HyperlinkedModelSerializer):
    encoded_videos = EncodedVideoSerializer(many=True, allow_add_remove=True)

    class Meta:
        model = Video
        lookup_field = "edx_video_id"
