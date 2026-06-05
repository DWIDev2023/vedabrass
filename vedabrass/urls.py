from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static

handler400 = "core.views.WebError400"
handler403 = "core.views.WebError403"
handler404 = "core.views.WebError404"
handler500 = "core.views.WebError500"

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', include('core.urls')),
    path('sonar/', include('django_sonar.urls')),
]

urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)