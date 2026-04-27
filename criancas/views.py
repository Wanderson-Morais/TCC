from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from .models import Crianca
from .forms import CriancaForm
from accounts.decorators import psicologo_required, adulto_required
from desempenho.models import Desempenho


@login_required
@adulto_required
def lista_criancas(request):
    user = request.user
    if user.role == 'psicologo':
        criancas = Crianca.objects.filter(psicologo=user)
    elif user.role == 'responsavel':
        criancas = user.criancas_responsavel.all()
    else:
        criancas = Crianca.objects.all()
    return render(request, 'criancas/lista.html', {'criancas': criancas})


@login_required
@psicologo_required
def criar_crianca(request):
    form = CriancaForm(request.POST or None, request.FILES or None, psicologo=request.user)
    if request.method == 'POST' and form.is_valid():
        crianca = form.save(commit=False)
        crianca.psicologo = request.user
        crianca.save()
        form.save_m2m()
        messages.success(request, f'Criança {crianca.nome} cadastrada com sucesso!')
        return redirect('detalhe_crianca', pk=crianca.pk)
    return render(request, 'criancas/form.html', {'form': form, 'titulo': 'Nova Criança'})


@login_required
@adulto_required
def detalhe_crianca(request, pk):
    user = request.user
    if user.role == 'psicologo':
        crianca = get_object_or_404(Crianca, pk=pk, psicologo=user)
    elif user.role == 'responsavel':
        crianca = get_object_or_404(Crianca, pk=pk, responsaveis=user)
    else:
        crianca = get_object_or_404(Crianca, pk=pk)

    qs = Desempenho.objects.filter(crianca=crianca).select_related('atividade', 'sessao').order_by('-created_at')

    total = qs.count()
    acertos = qs.filter(correto=True).count()
    taxa = round((acertos / total * 100) if total else 0, 1)

    desempenhos = qs[:20]

    return render(request, 'criancas/detalhe.html', {
        'crianca': crianca,
        'desempenhos': desempenhos,
        'total': total,
        'acertos': acertos,
        'taxa': taxa,
    })


@login_required
@psicologo_required
def editar_crianca(request, pk):
    crianca = _get_crianca_editavel(request, pk)
    form = CriancaForm(
        request.POST or None,
        request.FILES or None,
        instance=crianca,
        psicologo=crianca.psicologo,
    )
    if request.method == 'POST' and form.is_valid():
        form.save()
        messages.success(request, 'Dados atualizados.')
        return redirect('detalhe_crianca', pk=crianca.pk)
    return render(request, 'criancas/form.html', {'form': form, 'titulo': 'Editar Criança', 'crianca': crianca})


@login_required
@psicologo_required
def excluir_crianca(request, pk):
    crianca = _get_crianca_editavel(request, pk)
    if request.method == 'POST':
        crianca.delete()
        messages.success(request, f'Criança {crianca.nome} excluída.')
        return redirect('lista_criancas')
    return render(request, 'criancas/confirmar_exclusao.html', {'crianca': crianca})


def _get_crianca_editavel(request, pk):
    if request.user.is_superuser or request.user.role == 'admin':
        return get_object_or_404(Crianca, pk=pk)
    return get_object_or_404(Crianca, pk=pk, psicologo=request.user)
