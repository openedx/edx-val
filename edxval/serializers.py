"""
Serializers for Video Abstraction Layer

Serialization is usually sent through the VideoSerializer which uses the
EncodedVideoSerializer which uses the profile_name as it's profile field.
"""


from rest_framework import serializers
from rest_framework.fields import DateTimeField, IntegerField

from edxval.models import CourseVideo, EncodedVideo, Profile, TranscriptPreference, Video, VideoImage, VideoTranscript


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


class TranscriptSerializer(serializers.ModelSerializer):
    """
    Serializer for VideoTranscript objects
    """
    class Meta:
        model = VideoTranscript
        fields = ('video_id', 'url', 'language_code', 'provider', 'file_format')

    video_id = serializers.SerializerMethodField()
    url = serializers.SerializerMethodField()

    def get_video_id(self, transcript):
        """
        Returns an edx video ID for the related video.
        """
        return transcript.video.edx_video_id

    def get_url(self, transcript):
        """
        Retrieves the transcript url.
        """
        return transcript.url()

    def validate(self, data):  # pylint: disable=arguments-differ
        """
        Validates the transcript data.
        """
        video_id = self.context.get('video_id')
        video = Video.get_or_none(edx_video_id=video_id)
        if not video:
            raise serializers.ValidationError('Video "{video_id}" is not valid.'.format(video_id=video_id))

        data.update(video=video)
        return data

    def create(self, validated_data):
        """
        Create the video transcript.
        """
        return VideoTranscript.create(**validated_data)


class CourseSerializer(serializers.RelatedField):
    """
    Field for CourseVideo
    """
    def to_representation(self, course_video):  # pylint: disable=arguments-differ
        """
        Returns a serializable representation of a CourseVideo instance.
        """
        return {
            course_video.course_id: course_video.image_url()
        }

    def to_internal_value(self, data):
        """
        Convert data into CourseVideo instance and image filename tuple.
        """
        course_id = data
        course_video = image = ''
        if data:
            if isinstance(data, dict):
                (course_id, image), = list(data.items())

            course_video = CourseVideo(course_id=course_id)
            course_video.full_clean(exclude=['video'])

        return course_video, image


class VideoSerializer(serializers.ModelSerializer):
    """
    Serializer for Video object

    encoded_videos takes a list of dicts EncodedVideo data.
    """
    encoded_videos = EncodedVideoSerializer(many=True)
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

    class Meta:
        model = Video
        lookup_field = "edx_video_id"
        exclude = ('id',)

    def get_url(self, obj):
        """
        Return relative url for the object
        """
        return obj.get_absolute_url()

    def validate(self, data):  # pylint: disable=arguments-differ
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

        # Clean course_video list from any invalid data.
        course_videos = [(course_video, image) for course_video, image in data.get('courses', []) if course_video]
        data['courses'] = course_videos

        return data

    def create(self, validated_data):
        """
        Create the video and its nested resources.
        """
        courses = validated_data.pop("courses", [])
        encoded_videos = validated_data.pop("encoded_videos", [])

        video = Video.objects.create(**validated_data)

        EncodedVideo.objects.bulk_create(
            EncodedVideo(video=video, **video_data)
            for video_data in encoded_videos
        )

        # The CourseSerializer will already have converted the course data
        # to CourseVideo models, so we can just set the video and save.
        # Also create VideoImage objects if an image filename is present
        for course_video, image_name in courses:
            course_video.video = video
            course_video.save()
            if image_name:
                VideoImage.create_or_update(course_video, image_name)

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

        # Set courses
        # NOTE: for backwards compatibility with the DRF v2 behavior,
        # we do NOT delete existing course videos during the update.
        # Also update VideoImage objects if an image filename is present
        for course_video, image_name in validated_data.get("courses", []):
            course_video.video = instance
            course_video.save()
            if image_name:
                VideoImage.create_or_update(course_video, image_name)

        return instance


class TranscriptPreferenceSerializer(serializers.ModelSerializer):
    """
    Serializer for TranscriptPreference
    """

    class Meta:
        model = TranscriptPreference
        fields = (
            'course_id',
            'provider',
            'cielo24_fidelity',
            'cielo24_turnaround',
            'three_play_turnaround',
            'preferred_languages',
            'video_source_language',
            'modified',
        )

    preferred_languages = serializers.SerializerMethodField()

    def get_preferred_languages(self, transcript_preference):
        """
        Returns python list for preferred_languages model field.
        """
        return transcript_preference.preferred_languages
