from django.urls import path
from . import views

urlpatterns = [
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
    path('registro/psicologo/', views.registro_psicologo, name='registro_psicologo'),
    path('registro/responsavel/', views.registro_responsavel, name='registro_responsavel'),
    path('aguardando/', views.aguardando_aprovacao, name='aguardando_aprovacao'),
    path('admin/usuarios/', views.admin_usuarios, name='admin_usuarios'),
    path('admin/usuarios/<int:pk>/aprovar/', views.aprovar_psicologo, name='aprovar_psicologo'),
    path('admin/usuarios/<int:pk>/reprovar/', views.reprovar_psicologo, name='reprovar_psicologo'),
    path('admin/usuarios/<int:pk>/editar/', views.editar_usuario, name='editar_usuario'),
    path('admin/usuarios/<int:pk>/excluir/', views.excluir_usuario, name='excluir_usuario'),
]
