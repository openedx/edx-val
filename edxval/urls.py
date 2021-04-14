"""
Url file for django app edxval.
"""
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
]

if getattr(settings, 'TEST_ONLY_URLS', None):
    from edxval.pacts.views import provider_state
    urlpatterns.append(url(
        r'^pact/provider_states/$',
        provider_state,
        name='provider-state-view'
    ))
