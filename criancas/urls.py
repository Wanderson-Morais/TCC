from django.urls import path
from . import views

urlpatterns = [
    path('', views.lista_criancas, name='lista_criancas'),
    path('nova/', views.criar_crianca, name='criar_crianca'),
    path('<int:pk>/', views.detalhe_crianca, name='detalhe_crianca'),
    path('<int:pk>/editar/', views.editar_crianca, name='editar_crianca'),
    path('<int:pk>/excluir/', views.excluir_crianca, name='excluir_crianca'),
]
