"""
Serializers for Video Abstraction Layer

Serialization is usually sent through the VideoSerializer which uses the
EncodedVideoSerializer which uses the profile_name as it's profile field.
"""
from rest_framework import serializers
from django.core.exceptions import ValidationError

from edxval.models import Profile, Video, EncodedVideo, Subtitle, CourseVideo


class ProfileSerializer(serializers.ModelSerializer):
    """
    Serializer for Profile object.
    """
    class Meta:  # pylint: disable=C1001, C0111
        model = Profile
        fields = (
            "profile_name",
            "extension",
            "width",
            "height"
        )


class EncodedVideoSerializer(serializers.ModelSerializer):
    """
    Serializer for EncodedVideo object.

    Uses the profile_name as it's profile value instead of a Profile object.
    """
    profile = serializers.SlugRelatedField(slug_field="profile_name")

    class Meta:  # pylint: disable=C1001, C0111
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


class SubtitleSerializer(serializers.ModelSerializer):
    """
    Serializer for Subtitle objects
    """
    content_url = serializers.CharField(source='get_absolute_url', read_only=True)
    content = serializers.CharField(write_only=True)

    def validate_content(self, attrs, source):
        """
        Validate that the subtitle is in the correct format
        """
        value = attrs[source]
        if attrs.get('fmt') == 'sjson':
            import json
            try:
                loaded = json.loads(value)
            except ValueError:
                raise serializers.ValidationError("Not in JSON format")
            else:
                attrs[source] = json.dumps(loaded)
        return attrs

    class Meta:  # pylint: disable=C1001, C0111
        model = Subtitle
        lookup_field = "id"
        fields = (
            "fmt",
            "language",
            "content_url",
            "content",
        )


class CourseSerializer(serializers.RelatedField):
    """
    Field for CourseVideo
    """
    def to_native(self, value):
        return value.course_id

    def from_native(self, data):
        if data:
            return CourseVideo(course_id=data)


class VideoSerializer(serializers.ModelSerializer):
    """
    Serializer for Video object

    encoded_videos takes a list of dicts EncodedVideo data.
    """
    encoded_videos = EncodedVideoSerializer(many=True, allow_add_remove=True)
    subtitles = SubtitleSerializer(many=True, allow_add_remove=True, required=False)
    courses = CourseSerializer(many=True, read_only=False)
    url = serializers.SerializerMethodField('get_url')

    class Meta:  # pylint: disable=C1001, C0111
        model = Video
        lookup_field = "edx_video_id"
        exclude = ('id',)


    def get_url(self, obj):
        """
        Return relative url for the object
        """
        return obj.get_absolute_url()

    def restore_fields(self, data, files):
        """
        Overridden function used to check against duplicate profile names.

        Converts a dictionary of data into a dictionary of deserialized fields. Also
        checks if there are duplicate profile_name(s). If there is, the deserialization
        is rejected.
        """
        reverted_data = {}

        if data is not None and not isinstance(data, dict):
            self._errors['non_field_errors'] = ['Invalid data']
            return None

        try:
            profiles = [ev["profile"] for ev in data.get("encoded_videos", [])]
            if len(profiles) != len(set(profiles)):
                self._errors['non_field_errors'] = ['Invalid data: duplicate profiles']
        except KeyError:
            raise ValidationError("profile required for deserializing")
        except TypeError:
            raise ValidationError("profile field needs to be a profile_name (str)")

        for field_name, field in self.fields.items():
            field.initialize(parent=self, field_name=field_name)
            try:
                field.field_from_native(data, files, field_name, reverted_data)
            except ValidationError as err:
                self._errors[field_name] = list(err.messages)
        return reverted_data
