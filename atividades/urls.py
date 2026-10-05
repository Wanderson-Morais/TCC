from django.urls import path
from . import views

urlpatterns = [
    path('', views.lista_atividades, name='lista_atividades'),
    path('nova/', views.criar_atividade, name='criar_atividade'),
    path('<int:pk>/', views.detalhe_atividade, name='detalhe_atividade'),
    path('<int:pk>/editar/', views.editar_atividade, name='editar_atividade'),
    path('<int:pk>/excluir/', views.excluir_atividade, name='excluir_atividade'),
    path('cartoes/nova/', views.criar_atividade_cartoes, name='criar_atividade_cartoes'),
    path('cartoes/<int:pk>/', views.detalhe_atividade_cartoes, name='detalhe_atividade_cartoes'),
    path('cartoes/<int:pk>/editar/', views.editar_atividade_cartoes, name='editar_atividade_cartoes'),
    path('cartoes/<int:pk>/excluir/', views.excluir_atividade_cartoes, name='excluir_atividade_cartoes'),
    path('cenarios/nova/', views.criar_atividade_cenario, name='criar_atividade_cenario'),
    path('cenarios/<int:pk>/', views.detalhe_atividade_cenario, name='detalhe_atividade_cenario'),
    path('cenarios/<int:pk>/editar/', views.editar_atividade_cenario, name='editar_atividade_cenario'),
    path('cenarios/<int:pk>/excluir/', views.excluir_atividade_cenario, name='excluir_atividade_cenario'),
]
