from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.urls import include, path

handler403 = 'powerpoint.views.handler403'
handler404 = 'powerpoint.views.handler404'

urlpatterns = [
    path('', include('powerpoint.urls')),
    path('auth/', include('users.urls')),
    path('admin/', admin.site.urls),
    path('auth/', include('django.contrib.auth.urls'))
]

if settings.DEBUG:
    urlpatterns += static(
        settings.MEDIA_URL, document_root=settings.MEDIA_ROOT
    )
