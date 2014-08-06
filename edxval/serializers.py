"""
Serializers for Video Abstraction Layer
"""
from rest_framework import serializers
from django.core.exceptions import ValidationError

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

    def get_identity(self, data):
        """
        This hook is required for bulk update.
        We need to override the default, to use the slug as the identity.
        """
        return data.get('profile', None)


class VideoSerializer(serializers.HyperlinkedModelSerializer):
    encoded_videos = EncodedVideoSerializer(
        many=True,
        allow_add_remove=True
    )

    class Meta:
        model = Video
        lookup_field = "edx_video_id"

    def restore_fields(self, data, files):
        """
        Converts a dictionary of data into a dictionary of deserialized fields. Also
        checks if there are duplicate profile_name(s). If there is, the deserialization
        is rejected.
        """
        reverted_data = {}

        if data is not None and not isinstance(data, dict):
            self._errors['non_field_errors'] = ['Invalid data']
            return None

        profiles = [ev["profile"] for ev in data.get("encoded_videos", [])]
        if len(profiles) != len(set(profiles)):
            self._errors['non_field_errors'] = ['Invalid data: duplicate profiles']

        for field_name, field in self.fields.items():
            field.initialize(parent=self, field_name=field_name)
            try:
                field.field_from_native(data, files, field_name, reverted_data)
            except ValidationError as err:
                self._errors[field_name] = list(err.messages)
        return reverted_data
