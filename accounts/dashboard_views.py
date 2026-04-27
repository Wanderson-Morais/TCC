from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from criancas.models import Crianca
from atividades.models import Atividade
from sessoes.models import Sessao
from desempenho.models import Desempenho
from .models import CustomUser


@login_required
def dashboard(request):
    user = request.user

    if user.is_superuser or user.role == 'admin':
        context = {
            'total_psicologos': CustomUser.objects.filter(role='psicologo').count(),
            'psicologos_pendentes': CustomUser.objects.filter(role='psicologo', aprovado=False).count(),
            'total_responsaveis': CustomUser.objects.filter(role='responsavel').count(),
            'total_criancas': Crianca.objects.count(),
            'psicologos_lista': CustomUser.objects.filter(role='psicologo', aprovado=False).order_by('first_name')[:5],
        }
        return render(request, 'dashboard/admin.html', context)

    if user.role == 'psicologo':
        if not user.aprovado:
            return redirect('aguardando_aprovacao')
        criancas = Crianca.objects.filter(psicologo=user)
        context = {
            'criancas': criancas,
            'total_criancas': criancas.count(),
            'total_atividades': Atividade.objects.filter(psicologo=user).count(),
            'total_sessoes': Sessao.objects.filter(psicologo=user).count(),
            'ultimos_desempenhos': Desempenho.objects.filter(
                atividade__psicologo=user
            ).select_related('crianca', 'atividade').order_by('-created_at')[:5],
        }
        return render(request, 'dashboard/psicologo.html', context)

    if user.role == 'responsavel':
        criancas = user.criancas_responsavel.all()
        context = {
            'criancas': criancas,
            'ultimos_desempenhos': Desempenho.objects.filter(
                crianca__in=criancas
            ).select_related('crianca', 'atividade').order_by('-created_at')[:5],
        }
        return render(request, 'dashboard/responsavel.html', context)

    return redirect('login')
