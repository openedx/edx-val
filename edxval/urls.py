"""
Url file for django app edxval.
"""
from django.conf import settings
from django.urls import path, re_path

from edxval import views

urlpatterns = [
    path('videos/', views.VideoList.as_view(), name='video-list'),
    re_path(
        r'^videos/(?P<edx_video_id>[-\w]+)$',
        views.VideoDetail.as_view(),
        name='video-detail'
    ),
    path('videos/status/', views.VideoStatusView.as_view(),
         name='video-status-update'
         ),
    path('videos/missing-hls/', views.HLSMissingVideoView.as_view(),
         name='hls-missing-video'
         ),
    path('videos/course-transcripts/<str:course_id>/', views.CourseTranscriptsDetailView.as_view(),
         name='course-transcripts'
         ),
    path('videos/video-transcripts/create/', views.VideoTranscriptView.as_view(),
         name='create-video-transcript'
         ),
    path('videos/video-transcripts/', views.VideoTranscriptView.as_view(),
         name='video-transcripts'
         ),
    path('videos/video-images/update/', views.VideoImagesView.as_view(),
         name='update-video-images'
         ),
    path('videos/courses/<str:course_id>/video-ids', views.CourseVideoIDsView.as_view(),
         name='course-video-ids'
         ),
]

if getattr(settings, 'PROVIDER_STATES_SETUP_VIEW_URL', None):
    from edxval.pacts.views import provider_state
    urlpatterns.append(re_path(
        r'^pact/provider_states/$',
        provider_state,
        name='provider-state-view'
    ))
