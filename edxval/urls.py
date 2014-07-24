from django.conf.urls import patterns, include, url
from rest_framework.urlpatterns import format_suffix_patterns

from edxval import views

from django.contrib import admin
admin.autodiscover()

urlpatterns = patterns('',
    url(r'^edxval/video/$', views.VideoList.as_view(),
        name="video_view"),
    url(r'^edxval/video/(?P<edx_video_id>\w+)',
        views.VideoDetail.as_view(),
        name="video_detail_view"),
    url(r'^admin/', include(admin.site.urls)),
)

urlpatterns = format_suffix_patterns(urlpatterns)
