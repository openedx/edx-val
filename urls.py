from django.conf import settings
from django.conf.urls import patterns, include, url
from django.contrib import admin

admin.autodiscover()

urlpatterns = patterns(
    '',
    # Django Admin
    url(r'^admin/', include(admin.site.urls)),

    # Allow Django Rest Framework Auth login
    url(r'^api-auth/', include('rest_framework.urls', namespace='rest_framework')),

    # edx-val
    url(r'^edxval/', include('edxval.urls'))
)

# We need to do explicit setup of the Django debug toolbar because autodiscovery
# causes problems when you mix debug toolbar >= 1.0 + django < 1.7, and the
# admin uses autodiscovery. See:
# http://django-debug-toolbar.readthedocs.org/en/1.0/installation.html#explicit-setup
if settings.DEBUG:
    urlpatterns += patterns('',
        url(r'^__debug__/', include('debug_toolbar.urls')),
    )
