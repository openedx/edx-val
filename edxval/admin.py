"""
Admin file for django app edxval.
"""


from django.contrib import admin

from .models import (
    CourseVideo,
    EncodedVideo,
    Profile,
    ThirdPartyTranscriptCredentialsState,
    TranscriptPreference,
    Video,
    VideoImage,
    VideoTranscript,
)


@admin.register(Profile)
class ProfileAdmin(admin.ModelAdmin):
    """ Admin for profile """
    list_display = ('id', 'profile_name')
    list_display_links = ('id', 'profile_name')
    admin_order_field = 'profile_name'


class EncodedVideoInline(admin.TabularInline):
    """ Admin for EncodedVideo """
    model = EncodedVideo


class CourseVideoInline(admin.TabularInline):
    """ Admin for CourseVideo """
    model = CourseVideo
    extra = 0
    verbose_name = "Course"
    verbose_name_plural = "Courses"


@admin.register(Video)
class VideoAdmin(admin.ModelAdmin):
    """ Admin for Video """
    list_display = (
        'id', 'edx_video_id', 'client_video_id', 'duration', 'created', 'status'
    )
    list_display_links = ('id', 'edx_video_id')
    search_fields = ('id', 'edx_video_id', 'client_video_id', 'status')
    list_per_page = 50
    admin_order_field = 'edx_video_id'
    inlines = [CourseVideoInline, EncodedVideoInline]


@admin.register(VideoImage)
class VideoImageAdmin(admin.ModelAdmin):
    """ Admin for VideoImage """
    raw_id_fields = ('course_video', )
    list_display = ('get_course_video', 'image', 'generated_images')
    search_fields = ('id', 'course_video__course_id', 'course_video__video__edx_video_id', 'generated_images')

    @admin.display(
        description='Course Video',
        ordering='course_video',
    )
    def get_course_video(self, obj):
        """ get course video """
        return '"{course_id}" -- "{edx_video_id}" '.format(
            course_id=obj.course_video.course_id,
            edx_video_id=obj.course_video.video.edx_video_id
        )
    model = VideoImage
    verbose_name = 'Video Image'
    verbose_name_plural = 'Video Images'


@admin.register(CourseVideo)
class CourseVideoAdmin(admin.ModelAdmin):
    """ Admin for CourseVideo """
    list_display = ('course_id', 'get_video_id', 'is_hidden')
    search_fields = ('id', 'course_id', 'video__status', 'video__edx_video_id')

    @admin.display(
        description='edX Video Id',
        ordering='video',
    )
    def get_video_id(self, obj):
        """ get video id """
        return obj.video.edx_video_id
    model = CourseVideo
    verbose_name = 'Course Video'
    verbose_name_plural = 'Course Videos'


@admin.register(VideoTranscript)
class VideoTranscriptAdmin(admin.ModelAdmin):
    """ Admin for VideoTranscript """
    raw_id_fields = ('video',)
    list_display = ('get_video', 'language_code', 'provider', 'file_format')
    search_fields = ('id', 'video__edx_video_id', 'language_code')

    @admin.display(
        description='Video',
        ordering='video',
    )
    def get_video(self, transcript):
        """ get video """
        return transcript.video.edx_video_id if getattr(transcript, 'video', False) else ''
    model = VideoTranscript
    verbose_name = 'Video Transcript'
    verbose_name_plural = 'Video Transcripts'


@admin.register(TranscriptPreference)
class TranscriptPreferenceAdmin(admin.ModelAdmin):
    """ Admin for TranscriptPreference """
    list_display = ('course_id', 'provider', 'video_source_language', 'preferred_languages')

    model = TranscriptPreference


@admin.register(ThirdPartyTranscriptCredentialsState)
class ThirdPartyTranscriptCredentialsStateAdmin(admin.ModelAdmin):
    """ Admin for ThirdPartyTranscriptCredentialsState  """
    list_display = ('org', 'provider', 'has_creds', 'created', 'modified')

    model = ThirdPartyTranscriptCredentialsState
    verbose_name = 'Organization Transcript Credential State'
    verbose_name_plural = 'Organization Transcript Credentials State'
