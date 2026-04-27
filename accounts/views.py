from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login, logout, authenticate
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from .models import CustomUser
from .forms import LoginForm, RegistroPsicologoForm, RegistroResponsavelForm, EditarUsuarioForm
from .decorators import admin_required


def login_view(request):
    if request.user.is_authenticated:
        return redirect('dashboard')
    form = LoginForm(request, data=request.POST or None)
    if request.method == 'POST' and form.is_valid():
        user = form.get_user()
        login(request, user)
        return redirect('dashboard')
    return render(request, 'accounts/login.html', {'form': form})


def logout_view(request):
    logout(request)
    return redirect('login')


def registro_psicologo(request):
    form = RegistroPsicologoForm(request.POST or None)
    if request.method == 'POST' and form.is_valid():
        form.save()
        messages.success(request, 'Cadastro realizado! Aguarde a aprovação do administrador.')
        return redirect('login')
    return render(request, 'accounts/registro_psicologo.html', {'form': form})


def registro_responsavel(request):
    form = RegistroResponsavelForm(request.POST or None)
    if request.method == 'POST' and form.is_valid():
        user = form.save()
        login(request, user)
        messages.success(request, 'Cadastro realizado com sucesso!')
        return redirect('dashboard')
    return render(request, 'accounts/registro_responsavel.html', {'form': form})


@login_required
def aguardando_aprovacao(request):
    return render(request, 'accounts/aguardando_aprovacao.html')


# ─── Admin views ──────────────────────────────────────────────────────────────

@login_required
@admin_required
def admin_usuarios(request):
    usuarios = CustomUser.objects.exclude(is_superuser=True).order_by('role', 'first_name')
    return render(request, 'accounts/admin_usuarios.html', {'usuarios': usuarios})


@login_required
@admin_required
def aprovar_psicologo(request, pk):
    user = get_object_or_404(CustomUser, pk=pk, role=CustomUser.ROLE_PSICOLOGO)
    user.aprovado = True
    user.save()
    messages.success(request, f'Psicólogo {user.get_full_name()} aprovado.')
    return redirect('admin_usuarios')


@login_required
@admin_required
def reprovar_psicologo(request, pk):
    user = get_object_or_404(CustomUser, pk=pk, role=CustomUser.ROLE_PSICOLOGO)
    user.aprovado = False
    user.save()
    messages.warning(request, f'Psicólogo {user.get_full_name()} reprovado.')
    return redirect('admin_usuarios')


@login_required
@admin_required
def editar_usuario(request, pk):
    usuario = get_object_or_404(CustomUser, pk=pk)
    form = EditarUsuarioForm(request.POST or None, instance=usuario)
    if request.method == 'POST' and form.is_valid():
        form.save()
        messages.success(request, 'Usuário atualizado.')
        return redirect('admin_usuarios')
    return render(request, 'accounts/editar_usuario.html', {'form': form, 'usuario': usuario})


@login_required
@admin_required
def excluir_usuario(request, pk):
    usuario = get_object_or_404(CustomUser, pk=pk)
    if request.method == 'POST':
        nome = usuario.get_full_name() or usuario.username
        usuario.delete()
        messages.success(request, f'Usuário {nome} excluído.')
        return redirect('admin_usuarios')
    return render(request, 'accounts/confirmar_exclusao_usuario.html', {'usuario': usuario})
