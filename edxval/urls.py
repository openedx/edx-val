"""
Url file for django app edxval.
"""

from django.conf.urls import url

from edxval import views

urlpatterns = [
    url(r'^videos/$',
        views.VideoList.as_view(),
        name="video-list"
    ),
    url(
        r'^videos/(?P<edx_video_id>[-\w]+)$',
        views.VideoDetail.as_view(),
        name="video-detail"
    ),
    url(
        r'^videos/(?P<video__edx_video_id>[-\w]+)/(?P<language>[-_\w]+)$',
        views.SubtitleDetail.as_view(),
        name="subtitle-detail"
    ),
    url(
        r'^videos/(?P<edx_video_id>[-\w]+)/(?P<language>[-_\w]+)/subtitle$',
        views.get_subtitle,
        name="subtitle-content"
    ),
    url(
        r'^videos/video-images/update/$',
        views.VideoImagesView.as_view(),
        name='update-video-images'
    ),
]
