"""
Url file for django app edxval.
"""

from django.conf.urls import url

from edxval import views

urlpatterns = [
    url(r'^videos/$',
        views.VideoList.as_view(),
        name='video-list'
    ),
    url(
        r'^videos/(?P<edx_video_id>[-\w]+)$',
        views.VideoDetail.as_view(),
        name='video-detail'
    ),
    url(
        r'^videos/status/$',
        views.VideoStatusView.as_view(),
        name='video-status-update'
    ),
    url(
        r'^videos/video-transcripts/create/$',
        views.VideoTranscriptView.as_view(),
        name='create-video-transcript'
    ),
    url(
        r'^videos/video-images/update/$',
        views.VideoImagesView.as_view(),
        name='update-video-images'
    ),
]
