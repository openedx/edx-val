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
        r'^edxval/video/(?P<edx_video_id>[-\w]+)',
        views.VideoDetail.as_view(),
        name="video-detail"
    ),
    url(
    	r'^edxval/subtitle/(?P<id>[\d]+)$',
        views.SubtitleDetail.as_view(),
        name="subtitle-detail"
    ),
    url(r'^edxval/subtitle/(?P<subtitle_id>[\d]+)/content$',
        views.get_subtitle,
        name="subtitle-content"
    ),
)
