from django.urls import path
from . import views

urlpatterns = [
    path('', views.lista_sessoes, name='lista_sessoes'),
    path('nova/', views.criar_sessao, name='criar_sessao'),
    path('<int:pk>/', views.detalhe_sessao, name='detalhe_sessao'),
    path('<int:pk>/editar/', views.editar_sessao, name='editar_sessao'),
    path('<int:pk>/excluir/', views.excluir_sessao, name='excluir_sessao'),
]
