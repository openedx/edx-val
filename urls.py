from django.conf.urls import patterns, include, url

from edxval import views

urlpatterns = patterns(
    '',
    url(
        r'^video/$',
        views.VideoList.as_view(),
        name="video_view"
    ),
    url(
        r'^video/(?P<edx_video_id>\w+)',
        views.VideoDetail.as_view(),
        name="video_detail_view"
    )
)
