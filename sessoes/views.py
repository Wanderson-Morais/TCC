from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from .models import Sessao
from .forms import SessaoForm
from accounts.decorators import psicologo_required, adulto_required


@login_required
@adulto_required
def lista_sessoes(request):
    user = request.user
    if user.role == 'psicologo':
        sessoes = Sessao.objects.filter(psicologo=user).prefetch_related('atividades', 'criancas')
    else:
        criancas = user.criancas_responsavel.all()
        sessoes = Sessao.objects.filter(criancas__in=criancas).distinct().prefetch_related('atividades', 'criancas')
    return render(request, 'sessoes/lista.html', {'sessoes': sessoes})


@login_required
@psicologo_required
def criar_sessao(request):
    form = SessaoForm(request.POST or None, psicologo=request.user)
    if request.method == 'POST' and form.is_valid():
        sessao = form.save(commit=False)
        sessao.psicologo = request.user
        sessao.save()
        form.save()  # triggers save_m2m for atividades/criancas
        messages.success(request, f'Sessão "{sessao.titulo}" criada!')
        return redirect('detalhe_sessao', pk=sessao.pk)
    return render(request, 'sessoes/form.html', {'form': form, 'titulo': 'Nova Sessão'})


@login_required
@adulto_required
def detalhe_sessao(request, pk):
    user = request.user
    if user.role == 'psicologo':
        sessao = get_object_or_404(Sessao, pk=pk, psicologo=user)
    else:
        criancas = user.criancas_responsavel.all()
        sessao = get_object_or_404(Sessao, pk=pk, criancas__in=criancas)
    return render(request, 'sessoes/detalhe.html', {'sessao': sessao})


@login_required
@psicologo_required
def editar_sessao(request, pk):
    sessao = get_object_or_404(Sessao, pk=pk, psicologo=request.user)
    form = SessaoForm(request.POST or None, instance=sessao, psicologo=request.user)
    if request.method == 'POST' and form.is_valid():
        form.save()
        messages.success(request, 'Sessão atualizada.')
        return redirect('detalhe_sessao', pk=sessao.pk)
    return render(request, 'sessoes/form.html', {'form': form, 'titulo': 'Editar Sessão', 'sessao': sessao})


@login_required
@psicologo_required
def excluir_sessao(request, pk):
    sessao = get_object_or_404(Sessao, pk=pk, psicologo=request.user)
    if request.method == 'POST':
        sessao.delete()
        messages.success(request, 'Sessão excluída.')
        return redirect('lista_sessoes')
    return render(request, 'sessoes/confirmar_exclusao.html', {'sessao': sessao})
