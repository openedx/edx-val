"""
Admin file for django app edxval.
"""

from django.contrib import admin
from .models import Video, Profile, EncodedVideo, Subtitle, CourseVideo, VideoImage


class ProfileAdmin(admin.ModelAdmin):  # pylint: disable=C0111
    list_display = ('id', 'profile_name')
    list_display_links = ('id', 'profile_name')
    admin_order_field = 'profile_name'


class EncodedVideoInline(admin.TabularInline):  # pylint: disable=C0111
    model = EncodedVideo


class CourseVideoInline(admin.TabularInline):  # pylint: disable=C0111
    model = CourseVideo
    extra = 0
    verbose_name = "Course"
    verbose_name_plural = "Courses"


class VideoAdmin(admin.ModelAdmin):  # pylint: disable=C0111
    list_display = (
        'id', 'edx_video_id', 'client_video_id', 'duration', 'created', 'status'
    )
    list_display_links = ('id', 'edx_video_id')
    search_fields = ('id', 'edx_video_id', 'client_video_id')
    list_per_page = 50
    admin_order_field = 'edx_video_id'
    inlines = [CourseVideoInline, EncodedVideoInline]


class VideoImageAdmin(admin.ModelAdmin):
    model = VideoImage
    verbose_name = 'Video Image'
    verbose_name_plural = 'Video Images'

admin.site.register(Profile, ProfileAdmin)
admin.site.register(Video, VideoAdmin)
admin.site.register(Subtitle)
admin.site.register(VideoImage, VideoImageAdmin)
