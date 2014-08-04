"""
Serializers for Video Abstraction Layer
"""
from rest_framework import serializers
from rest_framework.serializers import ValidationError


from edxval.models import Profile, Video, EncodedVideo


class DisplayProfileName(serializers.WritableField):
    """
    Takes a Profile Object and returns only it's profile_name
    """
    def from_native(self, data):
        try:
            if isinstance(data, int):
                profile = Profile.objects.get(pk=data)
            elif isinstance(data, unicode):
                profile = Profile.objects.get(profile_name=str(data))
            return profile
        except Profile.DoesNotExist:
            error_message = "Profile does not exist: {0}".format(data)
            raise ValidationError(error_message)

    def to_native(self, data):
        return data.profile_name


class DisplayVideoName(serializers.WritableField):
    """
    Takes a Video Object and returns only it's profile_name
    """
    def from_native(self, data):
        #TODO change doc/function name or modify this function, currently
        #TODO takes a video pk and converts it to video Object.
        try:
            if isinstance(data, int):
                video = Video.objects.get(pk=data)
            return video
        except Video.DoesNotExist:
            error_message = "Video does not exist: {0}".format(data)
            raise ValidationError(error_message)

    def to_native(self, data):
        return data.edx_video_id


class ListField(serializers.WritableField):
    """
    Allows the use of a list as a serializer field.
    """
    def from_native(self, data):
        if isinstance(data, list):
            return data
        else:
            error_message = "Expecting a list: {0}".format(type(data))
            raise ValidationError(error_message)

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


class VideoSerializer(serializers.ModelSerializer):

    def restore_object(self, attrs, instance=None):
        """
        Given a dictionary of deserialized field values, either update
        an existing model instance, or create a new model instance.
        """
        if instance is not None:
            instance.edx_video_id = attrs.get('edx_video_id', instance.edx_video_id)
            instance.duration = attrs.get('duration', instance.duration)
            instance.client_video_id = attrs.get('client_video_id', instance.client_video_id)
            return instance
        return Video(**attrs)

    class Meta:
        model = Video
        fields = (
            "client_video_id",
            "duration",
            "edx_video_id"
        )


class EncodedVideoSerializer(serializers.ModelSerializer):
    """
    Used to serialize the EncodedVideo for the EncodedVideoSetSerializer
    """
    profile = DisplayProfileName()
    video = DisplayVideoName()

    def restore_object(self, attrs, instance=None):
        """
        Given a dictionary of deserialized field values, either update
        an existing model instance, or create a new model instance.
        """
        if instance is not None:
            #TODO Currently not updating Encodedvideo Object.
            instance.url = attrs.get('url', instance.url)
            instance.file_size = attrs.get('file_size', instance.file_size)
            instance.bitrate = attrs.get('bitrate', instance.bitrate)
            #TODO profile instance.profile = attrs.get('profile', instance.profile)
            return instance
        return EncodedVideo(**attrs)

    class Meta:
        model = EncodedVideo
        fields = (
            "url",
            "file_size",
            "bitrate",
            "profile",
            "video"

        )


class EncodedVideoSetSerializer(serializers.ModelSerializer):
    """
    Used to serialize a list of EncodedVideo objects it's foreign key Video Object.
    """
    edx_video_id = serializers.CharField(max_length=50)
    encoded_videos = EncodedVideoSerializer(required=False)


    class Meta:
        model = Video
        fields = (
            "duration",
            "client_video_id",
            "edx_video_id",
            "encoded_videos"
        )


class EncodedVideoSetDeserializer(serializers.Serializer):
    """
    Deserializes a dict of Video fields and list of EncodedVideos.

    Example:
    >>>data = dict(
    ...    client_video_id="Shallow Swordfish",
    ...    duration=122.00,
    ...    edx_video_id="supersoaker",
    ...        encoded_videos=[
    ...            dict(
    ...                url="https://www.swordsingers.com",
    ...                file_size=9000,
    ...                bitrate=42,
    ...                profile=1,
    ...            ),
    ...            dict(
    ...                url="https://www.swordsingers.com",
    ...                file_size=9000,
    ...                bitrate=42,
    ...                profile=2,
    ...            )
    ...        ]
    ...    )
    >>>serilizer = EncodedVideoSetDeserializer(data=data)
    >>>if serilizer.is_valid()
    >>>     serializer.save()
    >>>video = Video.objects.get(edx_video_id="supersoaker")
    >>>print EncodedVideoSetDeserializer(video).data
    {
        'duration': 122.0,
        'client_video_id': u'ShallowSwordfish',
        'edx_video_id': u'supersoaker',
        'encoded_videos': [
            {
                'url': u'https: //www.swordsingers.com',
                'file_size': 9000,
                'bitrate': 42,
                'profile': u'mobile',
                'video': u'supersoaker'
            },
            {
                'url': u'https: //www.swordsingers.com',
                'file_size': 9000,
                'bitrate': 42,
                'profile': u'desktop',
                'video': u'supersoaker'
            }
        ]
    }


    """
    client_video_id = serializers.CharField(max_length=50)
    duration = serializers.FloatField()
    edx_video_id = serializers.CharField(max_length=50)
    encoded_videos = ListField(required=False)

    def restore_object(self, attrs, instance=None):
        """
        Updates or creates video object and creates valid EncodedVideo objects.

        If the Video parameters are not valid, the errors are returns and the
        Video object is not created and the desrialization ends. If any of the
        EncodedVideo Parameters are invalid, the errors are returns and the
        EncodedVideos objects are not created.
        """
        #Get or create the Video object, else return errors
        try:
            instance = Video.objects.get(edx_video_id=attrs.get("edx_video_id"))
        except Video.DoesNotExist:
            instance = None
        video = VideoSerializer(
            data=dict(
                edx_video_id=attrs.get("edx_video_id"),
                duration=attrs.get("duration"),
                client_video_id=attrs.get("client_video_id")
            ),
            instance=instance
        )
        if video.is_valid():
            video.save()
        else:
            for key in video.errors:
                self.errors[key] = video.errors[key]
            return
        #Point encoded_videos to parent video
        if not "encoded_videos" in attrs:
            return video
        for item in attrs.get("encoded_videos"):
            item[u"video"] = Video.objects.get(edx_video_id=attrs.get("edx_video_id")).pk
        #Serialize EncodedVideos, else raise errors
        ev = EncodedVideoSerializer(data=attrs.get("encoded_videos"), many=True)
        if ev.is_valid():
            ev.save()
        else:
            self.errors["encoded_videos"] = ev.errors
        return video