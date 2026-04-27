from django.urls import path
from .dashboard_views import dashboard

urlpatterns = [
    path('', dashboard, name='dashboard'),
]
