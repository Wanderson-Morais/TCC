from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from .models import Atividade, ImagemEmocao
from .forms import AtividadeForm, ImagemFormSet
from accounts.decorators import psicologo_required, adulto_required


@login_required
@adulto_required
def lista_atividades(request):
    user = request.user
    if user.role == 'psicologo':
        atividades = Atividade.objects.filter(psicologo=user).prefetch_related('imagens')
    else:
        # responsavel vê atividades das sessões vinculadas às suas crianças
        from sessoes.models import Sessao
        criancas = user.criancas_responsavel.all()
        sessoes = Sessao.objects.filter(criancas__in=criancas)
        atividades = Atividade.objects.filter(sessoes__in=sessoes).distinct()
    return render(request, 'atividades/lista.html', {'atividades': atividades})


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
