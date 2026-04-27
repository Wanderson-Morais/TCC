from django.urls import path
from . import views

urlpatterns = [
    path('', views.lista_atividades, name='lista_atividades'),
    path('nova/', views.criar_atividade, name='criar_atividade'),
    path('<int:pk>/', views.detalhe_atividade, name='detalhe_atividade'),
    path('<int:pk>/editar/', views.editar_atividade, name='editar_atividade'),
    path('<int:pk>/excluir/', views.excluir_atividade, name='excluir_atividade'),
]
