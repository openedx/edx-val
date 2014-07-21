"""
"""
from django.db import transaction
from rest_framework import serializers
from edxval.models import Video, Profile, EncodedVideo


class ValidationError(Exception):
    """
    Error validating dict
    """
    pass


class KeyValueError(ValidationError):
    """
    The fields are invalid
    """
    pass


class InternalError(ValidationError):
    """
    Dict cannot be deserialized
    """
    pass


class VideoSerializer(serializers.ModelSerializer):
    video_prefix = serializers.CharField(max_length=50)

    class Meta:
        model = Video
        fields = (
            "client_title",
            "duration",
        )

    def validate_video_prefix(self, attrs, source):
        value = attrs[source]
        if len(value) == 20:
            if value[12] == "-":
                return True
        raise serializers.ValidationError("Invalid video id: {0}".format(value))


class ProfileSerializer(serializers.ModelSerializer):
    class Meta:
        model = Profile
        fields = (
            "profile_id",
            "profile_name",
            "extension",
            "width",
            "height"
        )


class OnlyEncodedVideoSerializer(serializers.ModelSerializer):
    """
    Used to validate non foreign key fields.
    """
    edx_video_id = serializers.CharField(max_length=50)

    class Meta:
        model = EncodedVideo
        fields = (
            "created",
            "modified",
            "url",
            "file_size",
            "bitrate",
        )


class EncodedVideoSerializer(serializers.ModelSerializer):

    profile = ProfileSerializer()
    video = VideoSerializer()

    class Meta:
        model = EncodedVideo
        fields = (
            "edx_video_id",
            "created",
            "modified",
            "url",
            "file_size",
            "bitrate",
            "profile",
            "video"
        )
        depth = 1

    def validate_video_id(self, attrs, source):
        value = attrs[source]
        if len(value) == 24:
            if value[12] == "-":
                if value[20] == "_":
                    return True
        raise serializers.ValidationError("Invalid video id: {0}".format(value))


def validate_video_upload_types(video_dict, encoded_dict, profile_info):
    """
    Checks the parameters for correct types

    Args:
        video_dict (dict): serialized video object
        encoded_dict (dict): serialized encoded video object without foreign keys
        profile_info (str): name of the profile
    Returns:
       tuple of (is_valid, errors), where `is_valid` is a bool
        and `errors` is a list of error messages.
    """
    errors = []

    if not isinstance(video_dict, dict):
        errors.append(u"video_dict must be a dictionary.")
    if not isinstance(encoded_dict, dict):
        errors.append(u"encoded_dict must be a dictionary.")
    if not isinstance(profile_info, str):
        errors.append(u"profile_info must be a string.")

    is_valid = (len(errors) == 0)
    return is_valid, errors


def validate_video_upload_fields(video_dict, encoded_dict, profile_info):
    """
    Checks the fields with serializers

    Args:
        video_dict (dict): serialized video object
        encoded_dict (dict): serialized encoded video object without foreign keys
        profile_info (str): name of the profile
    Returns:
       boolean: True if successful
    Raises:
        InvalidFieldsError
    """
    try:
        profile = Profile.objects.get(profile_id=profile_info)
    except Profile.DoesNotExist:
        error_message = u"No profile found for: {0}".format(profile_info)
        raise KeyValueError(error_message)
    if not VideoSerializer(data=video_dict).is_valid():
        error_message = u"Invalid video fields: {0}".format(
            VideoSerializer(data=video_dict).errors)
        raise KeyValueError(error_message)
    if not OnlyEncodedVideoSerializer(data=encoded_dict).is_valid():
        error_message = u"Invalid encoded video fields: {0}".format(
            OnlyEncodedVideoSerializer(data=encoded_dict).errors)
        raise KeyValueError(error_message)
    return True

@transaction.commit_on_success
def deserialize_video_upload(video_dict, encoded_dict, profile_info):
    """
    Deserializes given parameters into an EncodedVideo object

    Args:
        video_dict (dict): serialized video object
        encoded_dict (dict): serialized encoded video object without foreign keys
        profile_info (str): name of the profile

    Returns:
        A tuple of (action, result), where action is a string, and result is a
        serialized object.
    """
    action = None
    is_valid, errors = validate_video_upload_types(
        video_dict, encoded_dict, profile_info)
    if not is_valid:
        raise ValidationError("; ".join(errors))
    if validate_video_upload_fields(video_dict, encoded_dict, profile_info):
        p = Profile.objects.get(profile_id=profile_info)
        try:
            v = Video.objects.get(video_prefix=video_dict.get("video_prefix"))
        except Video.DoesNotExist:
            v = Video.objects.create(**video_dict)
        try:
            EncodedVideo.objects.get(edx_video_id=encoded_dict.get('edx_video_id'))
            try:
                EncodedVideo.objects.update(video=v, profile=p, **encoded_dict)
                action = "updated"
                e = EncodedVideo.objects.get(edx_video_id=encoded_dict.get('edx_video_id'))
            except:
                raise InternalError("Unable to update.")
        except EncodedVideo.DoesNotExist:
            try:
                e = EncodedVideo.objects.create(video=v, profile=p, **encoded_dict)
                action = "created"
            except:
                raise InternalError("Unable to deserialize.")
    result = EncodedVideoSerializer(e).data
    return action, result









