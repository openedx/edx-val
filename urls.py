from django.conf.urls import patterns, include, url

from django.contrib import admin
admin.autodiscover()

urlpatterns = patterns('',
    url(r'^edxval/', include('edxval.urls')),
    url(r'^admin/', include(admin.site.urls)),
<<<<<<< HEAD
)
=======
)
>>>>>>> fbc37f7... Added POST/GET for video models
