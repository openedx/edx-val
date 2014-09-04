"""
Url file for django app edxval.
"""

from django.conf.urls import patterns, url

from edxval import views

urlpatterns = patterns(
    '',
    url(
        r'^edxval/video/$',
        views.VideoList.as_view(),
        name="video-list"
    ),
    url(
        r'^edxval/video/(?P<edx_video_id>[-\w]+)$',
        views.VideoDetail.as_view(),
        name="video-detail"
    ),
    url(
    	r'^edxval/video/(?P<video__edx_video_id>[-\w]+)/(?P<language>[-_\w]+)$',
        views.SubtitleDetail.as_view(),
        name="subtitle-detail"
    ),
    url(
    	r'^edxval/video/(?P<edx_video_id>[-\w]+)/(?P<language>[-_\w]+)/subtitle$',
        views.get_subtitle,
        name="subtitle-content"
    ),
    url(
        r'^edxval/course/(?P<course_id>[-\w/]+)$',
        views.CourseVideoList.as_view(),
        name="course-video-list"
    ),

)
