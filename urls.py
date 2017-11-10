from django.conf.urls import include, url
from django.contrib import admin


urlpatterns = [
    # Django Admin
    url(r'^admin/', include(admin.site.urls)),

    # Allow Django Rest Framework Auth login
    url(r'^api-auth/', include('rest_framework.urls', namespace='rest_framework')),

    # edx-val
    url(r'^edxval/', include('edxval.urls'))
]
