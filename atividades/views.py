from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from .models import Atividade, AtividadeCartoes, AtividadeCenario, ImagemEmocao
from .forms import (
    AtividadeForm, ImagemFormSet, AtividadeCartoesForm, CartaoFormSet,
    AtividadeCenarioForm, CenarioFormSet,
)
from accounts.decorators import psicologo_required, adulto_required


@login_required
@adulto_required
def lista_atividades(request):
    user = request.user
    if user.role == 'psicologo':
        atividades = Atividade.objects.filter(psicologo=user).prefetch_related('imagens')
        atividades_cartoes = AtividadeCartoes.objects.filter(psicologo=user).prefetch_related('cartoes')
        atividades_cenarios = AtividadeCenario.objects.filter(psicologo=user).prefetch_related('cenarios')
    else:
        # responsavel vê atividades das sessões vinculadas às suas crianças
        from sessoes.models import Sessao
        criancas = user.criancas_responsavel.all()
        sessoes = Sessao.objects.filter(criancas__in=criancas)
        atividades = Atividade.objects.filter(sessoes__in=sessoes).distinct()
        atividades_cartoes = AtividadeCartoes.objects.filter(sessoes__in=sessoes).distinct()
        atividades_cenarios = AtividadeCenario.objects.filter(sessoes__in=sessoes).distinct()
    return render(request, 'atividades/lista.html', {
        'atividades': atividades,
        'atividades_cartoes': atividades_cartoes,
        'atividades_cenarios': atividades_cenarios,
    })


@login_required
@psicologo_required
def criar_atividade(request):
    form = AtividadeForm(request.POST or None)
    formset = ImagemFormSet(request.POST or None, request.FILES or None)
    if request.method == 'POST' and form.is_valid() and formset.is_valid():
        atividade = form.save(commit=False)
        atividade.psicologo = request.user
        atividade.save()
        formset.instance = atividade
        formset.save()
        messages.success(request, f'Atividade "{atividade.titulo}" criada!')
        return redirect('detalhe_atividade', pk=atividade.pk)
    return render(request, 'atividades/form.html', {
        'form': form,
        'formset': formset,
        'titulo': 'Nova Atividade',
    })


@login_required
@adulto_required
def detalhe_atividade(request, pk):
    user = request.user
    if user.role == 'psicologo':
        atividade = get_object_or_404(Atividade, pk=pk, psicologo=user)
    else:
        from sessoes.models import Sessao
        criancas = user.criancas_responsavel.all()
        sessoes = Sessao.objects.filter(criancas__in=criancas)
        atividade = get_object_or_404(Atividade, pk=pk, sessoes__in=sessoes)
    imagens = atividade.imagens.all()
    return render(request, 'atividades/detalhe.html', {'atividade': atividade, 'imagens': imagens})


@login_required
@psicologo_required
def editar_atividade(request, pk):
    atividade = get_object_or_404(Atividade, pk=pk, psicologo=request.user)
    form = AtividadeForm(request.POST or None, instance=atividade)
    formset = ImagemFormSet(request.POST or None, request.FILES or None, instance=atividade)
    if request.method == 'POST' and form.is_valid() and formset.is_valid():
        form.save()
        formset.save()
        messages.success(request, 'Atividade atualizada.')
        return redirect('detalhe_atividade', pk=atividade.pk)
    return render(request, 'atividades/form.html', {
        'form': form,
        'formset': formset,
        'titulo': 'Editar Atividade',
        'atividade': atividade,
    })


@login_required
@psicologo_required
def excluir_atividade(request, pk):
    atividade = get_object_or_404(Atividade, pk=pk, psicologo=request.user)
    if request.method == 'POST':
        atividade.delete()
        messages.success(request, 'Atividade excluída.')
        return redirect('lista_atividades')
    return render(request, 'atividades/confirmar_exclusao.html', {'atividade': atividade})


# ─── Cartões Correspondentes ──────────────────────────────────────────────────

@login_required
@psicologo_required
def criar_atividade_cartoes(request):
    form = AtividadeCartoesForm(request.POST or None)
    formset = CartaoFormSet(request.POST or None, request.FILES or None)
    if request.method == 'POST' and form.is_valid() and formset.is_valid():
        atividade = form.save(commit=False)
        atividade.psicologo = request.user
        atividade.save()
        formset.instance = atividade
        formset.save()
        messages.success(request, f'Atividade "{atividade.titulo}" criada!')
        return redirect('detalhe_atividade_cartoes', pk=atividade.pk)
    return render(request, 'atividades/cartoes_form.html', {
        'form': form,
        'formset': formset,
        'titulo': 'Nova Atividade de Cartões',
    })


@login_required
@adulto_required
def detalhe_atividade_cartoes(request, pk):
    user = request.user
    if user.role == 'psicologo':
        atividade = get_object_or_404(AtividadeCartoes, pk=pk, psicologo=user)
    else:
        from sessoes.models import Sessao
        criancas = user.criancas_responsavel.all()
        sessoes = Sessao.objects.filter(criancas__in=criancas)
        atividade = get_object_or_404(AtividadeCartoes.objects.distinct(), pk=pk, sessoes__in=sessoes)
    return render(request, 'atividades/cartoes_detalhe.html', {
        'atividade': atividade,
        'cartoes': atividade.cartoes.all(),
    })


@login_required
@psicologo_required
def editar_atividade_cartoes(request, pk):
    atividade = get_object_or_404(AtividadeCartoes, pk=pk, psicologo=request.user)
    form = AtividadeCartoesForm(request.POST or None, instance=atividade)
    formset = CartaoFormSet(request.POST or None, request.FILES or None, instance=atividade)
    if request.method == 'POST' and form.is_valid() and formset.is_valid():
        form.save()
        formset.save()
        messages.success(request, 'Atividade atualizada.')
        return redirect('detalhe_atividade_cartoes', pk=atividade.pk)
    return render(request, 'atividades/cartoes_form.html', {
        'form': form,
        'formset': formset,
        'titulo': 'Editar Atividade de Cartões',
        'atividade': atividade,
    })


@login_required
@psicologo_required
def excluir_atividade_cartoes(request, pk):
    atividade = get_object_or_404(AtividadeCartoes, pk=pk, psicologo=request.user)
    if request.method == 'POST':
        atividade.delete()
        messages.success(request, 'Atividade excluída.')
        return redirect('lista_atividades')
    return render(request, 'atividades/cartoes_confirmar_exclusao.html', {'atividade': atividade})


# ─── Organização de Emoções em Cenários ───────────────────────────────────────

@login_required
@psicologo_required
def criar_atividade_cenario(request):
    form = AtividadeCenarioForm(request.POST or None)
    formset = CenarioFormSet(request.POST or None, request.FILES or None)
    if request.method == 'POST' and form.is_valid() and formset.is_valid():
        atividade = form.save(commit=False)
        atividade.psicologo = request.user
        atividade.save()
        formset.instance = atividade
        formset.save()
        messages.success(request, f'Atividade "{atividade.titulo}" criada!')
        return redirect('detalhe_atividade_cenario', pk=atividade.pk)
    return render(request, 'atividades/cenarios_form.html', {
        'form': form,
        'formset': formset,
        'titulo': 'Nova Atividade de Cenários',
    })


@login_required
@adulto_required
def detalhe_atividade_cenario(request, pk):
    user = request.user
    if user.role == 'psicologo':
        atividade = get_object_or_404(AtividadeCenario, pk=pk, psicologo=user)
    else:
        from sessoes.models import Sessao
        criancas = user.criancas_responsavel.all()
        sessoes = Sessao.objects.filter(criancas__in=criancas)
        atividade = get_object_or_404(AtividadeCenario.objects.distinct(), pk=pk, sessoes__in=sessoes)
    return render(request, 'atividades/cenarios_detalhe.html', {
        'atividade': atividade,
        'cenarios': atividade.cenarios.all(),
    })


@login_required
@psicologo_required
def editar_atividade_cenario(request, pk):
    atividade = get_object_or_404(AtividadeCenario, pk=pk, psicologo=request.user)
    form = AtividadeCenarioForm(request.POST or None, instance=atividade)
    formset = CenarioFormSet(request.POST or None, request.FILES or None, instance=atividade)
    if request.method == 'POST' and form.is_valid() and formset.is_valid():
        form.save()
        formset.save()
        messages.success(request, 'Atividade atualizada.')
        return redirect('detalhe_atividade_cenario', pk=atividade.pk)
    return render(request, 'atividades/cenarios_form.html', {
        'form': form,
        'formset': formset,
        'titulo': 'Editar Atividade de Cenários',
        'atividade': atividade,
    })


@login_required
@psicologo_required
def excluir_atividade_cenario(request, pk):
    atividade = get_object_or_404(AtividadeCenario, pk=pk, psicologo=request.user)
    if request.method == 'POST':
        atividade.delete()
        messages.success(request, 'Atividade excluída.')
        return redirect('lista_atividades')
    return render(request, 'atividades/cenarios_confirmar_exclusao.html', {'atividade': atividade})
