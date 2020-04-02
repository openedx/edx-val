"""
Url file for django app edxval.
"""

from __future__ import absolute_import

from django.conf import settings
from django.conf.urls import url

from edxval import views

urlpatterns = [
    url(r'^videos/$', views.VideoList.as_view(), name='video-list'),
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
        r'^videos/missing-hls/$',
        views.HLSMissingVideoView.as_view(),
        name='hls-missing-video'
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
    url(
        r'^videos/transcript-credentials/(?P<provider>[\w]*)/(?P<org>[\w]*)$',
        views.TranscriptCredentialsView.as_view(),
        name='transcript-credentials'
    ),
    url(
        r'^videos/transcript-preferences/{}$'.format(settings.COURSE_ID_PATTERN),
        views.TranscriptPreferenceView.as_view(),
        name='transcript-preferences'
    )
]
