from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from django.shortcuts import redirect

urlpatterns = [
    path('admin/', admin.site.urls),
    path('accounts/', include('accounts.urls')),
    path('criancas/', include('criancas.urls')),
    path('atividades/', include('atividades.urls')),
    path('sessoes/', include('sessoes.urls')),
    path('desempenho/', include('desempenho.urls')),
    path('dashboard/', include('accounts.dashboard_urls')),
    path('', lambda request: redirect('dashboard')),
] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
