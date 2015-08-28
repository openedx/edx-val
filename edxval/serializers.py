"""
Serializers for Video Abstraction Layer

Serialization is usually sent through the VideoSerializer which uses the
EncodedVideoSerializer which uses the profile_name as it's profile field.
"""
from rest_framework import serializers
from rest_framework.fields import IntegerField, DateTimeField

from edxval.models import Profile, Video, EncodedVideo, Subtitle, CourseVideo


class EncodedVideoSerializer(serializers.ModelSerializer):
    """
    Serializer for EncodedVideo object.

    Uses the profile_name as it's profile value instead of a Profile object.
    """
    profile = serializers.SlugRelatedField(
        slug_field="profile_name",
        queryset=Profile.objects.all()
    )

    # Django Rest Framework v3 doesn't enforce minimum values for
    # PositiveIntegerFields, so we need to specify the min value explicitly.
    bitrate = IntegerField(min_value=0)
    file_size = IntegerField(min_value=0)

    # Django Rest Framework v3 converts datetimes to unicode by default.
    # Specify format=None to leave them as datetimes.
    created = DateTimeField(required=False, format=None)
    modified = DateTimeField(required=False, format=None)

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

    def validate(self, data):
        """
        Validate that the subtitle is in the correct format
        """
        value = data.get("content")
        if data.get("fmt") == "sjson":
            import json
            try:
                loaded = json.loads(value)
            except ValueError:
                raise serializers.ValidationError("Not in JSON format")
            else:
                data["content"] = json.dumps(loaded)
        return data

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
    def to_representation(self, value):
        return value.course_id

    def to_internal_value(self, data):
        if data:
            course_video = CourseVideo(course_id=data)
            course_video.full_clean(exclude=["video"])
            return course_video


class VideoSerializer(serializers.ModelSerializer):
    """
    Serializer for Video object

    encoded_videos takes a list of dicts EncodedVideo data.
    """
    encoded_videos = EncodedVideoSerializer(many=True)
    subtitles = SubtitleSerializer(many=True, required=False)
    courses = CourseSerializer(
        many=True,
        read_only=False,
        required=False,
        queryset=CourseVideo.objects.all()
    )
    url = serializers.SerializerMethodField()

    # Django Rest Framework v3 converts datetimes to unicode by default.
    # Specify format=None to leave them as datetimes.
    created = DateTimeField(required=False, format=None)

    class Meta:  # pylint: disable=C1001, C0111
        model = Video
        lookup_field = "edx_video_id"
        exclude = ('id',)

    def get_url(self, obj):
        """
        Return relative url for the object
        """
        return obj.get_absolute_url()

    def validate(self, data):
        """
        Check that the video data is valid.
        """
        if data is not None and not isinstance(data, dict):
            raise serializers.ValidationError("Invalid data")

        try:
            profiles = [ev["profile"] for ev in data.get("encoded_videos", [])]
            if len(profiles) != len(set(profiles)):
                raise serializers.ValidationError("Invalid data: duplicate profiles")
        except KeyError:
            raise serializers.ValidationError("profile required for deserializing")
        except TypeError:
            raise serializers.ValidationError("profile field needs to be a profile_name (str)")

        return data

    def create(self, validated_data):
        """
        Create the video and its nested resources.
        """
        courses = validated_data.pop("courses", [])
        encoded_videos = validated_data.pop("encoded_videos", [])
        subtitles = validated_data.pop("subtitles", [])

        video = Video.objects.create(**validated_data)

        EncodedVideo.objects.bulk_create(
            EncodedVideo(video=video, **video_data)
            for video_data in encoded_videos
        )

        Subtitle.objects.bulk_create(
            Subtitle(video=video, **subtitle_data)
            for subtitle_data in subtitles
        )

        # The CourseSerializer will already have converted the course data
        # to CourseVideo models, so we can just set the video and save.
        for course_video in courses:
            course_video.video = video
            course_video.save()

        return video

    def update(self, instance, validated_data):
        """
        Update an existing video resource.
        """
        instance.status = validated_data["status"]
        instance.client_video_id = validated_data["client_video_id"]
        instance.duration = validated_data["duration"]
        instance.save()

        # Set encoded videos
        instance.encoded_videos.all().delete()
        EncodedVideo.objects.bulk_create(
            EncodedVideo(video=instance, **video_data)
            for video_data in validated_data.get("encoded_videos", [])
        )

        # Set subtitles
        instance.subtitles.all().delete()
        Subtitle.objects.bulk_create(
            Subtitle(video=instance, **subtitle_data)
            for subtitle_data in validated_data.get("subtitles", [])
        )

        # Set courses
        # NOTE: for backwards compatibility with the DRF v2 behavior,
        # we do NOT delete existing course videos during the update.
        for course_video in validated_data.get("courses", []):
            course_video.video = instance
            course_video.save()

        return instance
