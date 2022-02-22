from django.contrib import admin
from django.urls import include, path

urlpatterns = [
    # Django Admin
    path('admin/', admin.site.urls),

    # Allow Django Rest Framework Auth login
    path('api-auth/', include('rest_framework.urls', namespace='rest_framework')),

    # edx-val
    path('edxval/', include('edxval.urls'))
]
