from functools import wraps
from django.shortcuts import redirect
from django.contrib import messages


def role_required(*roles):
    def decorator(view_func):
        @wraps(view_func)
        def wrapper(request, *args, **kwargs):
            if not request.user.is_authenticated:
                return redirect('login')
            if request.user.role not in roles and not request.user.is_superuser:
                messages.error(request, 'Você não tem permissão para acessar esta página.')
                return redirect('dashboard')
            if request.user.role == 'psicologo' and not request.user.aprovado and not request.user.is_superuser:
                messages.warning(request, 'Sua conta ainda não foi aprovada pelo administrador.')
                return redirect('aguardando_aprovacao')
            return view_func(request, *args, **kwargs)
        return wrapper
    return decorator


def psicologo_required(view_func):
    return role_required('psicologo')(view_func)


def responsavel_required(view_func):
    return role_required('responsavel')(view_func)


def admin_required(view_func):
    return role_required('admin')(view_func)


def adulto_required(view_func):
    return role_required('psicologo', 'responsavel', 'admin')(view_func)
