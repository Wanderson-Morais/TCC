from django.urls import path
from . import views

urlpatterns = [
    path('relatorio/', views.relatorio_geral, name='relatorio_geral'),
    path('crianca/<int:crianca_pk>/', views.relatorio_crianca, name='relatorio_crianca'),
    path('crianca/<int:crianca_pk>/atividade/<int:atividade_pk>/executar/', views.executar_atividade, name='executar_atividade'),
    path('crianca/<int:crianca_pk>/atividade/<int:atividade_pk>/resposta/', views.registrar_resposta, name='registrar_resposta'),
]
