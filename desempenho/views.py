import json
import random
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.views.decorators.http import require_POST
from django.contrib import messages
from django.db.models import Count, Q
from .models import Desempenho, DesempenhoCartoes, DesempenhoCenario
from atividades.models import (
    EMOCAO_CHOICES, Atividade, AtividadeCartoes, AtividadeCenario,
    CartaoEmocao, CenarioEmocao, ImagemEmocao,
)
from criancas.models import Crianca
from sessoes.models import Sessao
from accounts.decorators import adulto_required, psicologo_required


# ─── Execução de Atividade ────────────────────────────────────────────────────

@login_required
@adulto_required
def executar_atividade(request, crianca_pk, atividade_pk):
    from django.urls import reverse
    crianca = _get_crianca_or_403(request, crianca_pk)
    atividade = get_object_or_404(Atividade, pk=atividade_pk)
    sessao_pk = request.GET.get('sessao')
    sessao = None
    proxima_url = None
    indice_atual = None
    total_atividades = None

    if sessao_pk:
        sessao = Sessao.objects.filter(pk=sessao_pk).first()

    if sessao:
        atividades_sessao = list(
            sessao.atividades.order_by('sessaoatividade__ordem', 'titulo')
        )
        total_atividades = len(atividades_sessao)
        ids = [a.pk for a in atividades_sessao]
        if atividade_pk in ids:
            pos = ids.index(atividade_pk)
            indice_atual = pos + 1
            if pos + 1 < total_atividades:
                proxima = atividades_sessao[pos + 1]
                proxima_url = (
                    reverse('executar_atividade', kwargs={
                        'crianca_pk': crianca_pk,
                        'atividade_pk': proxima.pk,
                    }) + f'?sessao={sessao.pk}'
                )

    imagens = list(atividade.imagens.all())
    if not imagens:
        messages.warning(request, 'Esta atividade não possui imagens cadastradas.')
        return redirect('detalhe_atividade', pk=atividade.pk)

    return render(request, 'desempenho/executar.html', {
        'crianca': crianca,
        'atividade': atividade,
        'imagens': imagens,
        'sessao': sessao,
        'proxima_url': proxima_url,
        'indice_atual': indice_atual,
        'total_atividades': total_atividades,
    })


@login_required
@adulto_required
@require_POST
def registrar_resposta(request, crianca_pk, atividade_pk):
    crianca = _get_crianca_or_403(request, crianca_pk)
    atividade = get_object_or_404(Atividade, pk=atividade_pk)

    try:
        body = json.loads(request.body)
    except (json.JSONDecodeError, AttributeError):
        body = request.POST

    imagem_id = body.get('imagem_id')
    tempo = body.get('tempo_resposta')
    sessao_id = body.get('sessao_id')

    imagem_selecionada = None
    correto = False
    if imagem_id:
        imagem_selecionada = ImagemEmocao.objects.filter(pk=imagem_id, atividade=atividade).first()
        if imagem_selecionada:
            correto = imagem_selecionada.correta

    sessao = None
    if sessao_id:
        sessao = Sessao.objects.filter(pk=sessao_id).first()

    Desempenho.objects.create(
        crianca=crianca,
        atividade=atividade,
        sessao=sessao,
        imagem_selecionada=imagem_selecionada,
        correto=correto,
        tempo_resposta=float(tempo) if tempo else None,
        executado_por=request.user,
    )

    return JsonResponse({'correto': correto, 'emocao_correta': atividade.emocao_correta})


# ─── Cartões Correspondentes ──────────────────────────────────────────────────

@login_required
@adulto_required
def executar_cartoes(request, crianca_pk, atividade_pk):
    crianca = _get_crianca_or_403(request, crianca_pk)
    atividade = _get_atividade_or_404(request, AtividadeCartoes, crianca, atividade_pk)
    sessao = _get_sessao(request.GET.get('sessao'), crianca, atividades_cartoes=atividade)

    cartoes = list(atividade.cartoes.all())
    if len(cartoes) < 2:
        messages.warning(request, 'Esta atividade precisa de pelo menos 2 cartões.')
        return redirect('detalhe_atividade_cartoes', pk=atividade.pk)

    # Palavras e imagens em ordens independentes, para a posição não entregar o par
    palavras = cartoes[:]
    imagens = cartoes[:]
    random.shuffle(palavras)
    random.shuffle(imagens)

    return render(request, 'desempenho/executar_cartoes.html', {
        'crianca': crianca,
        'atividade': atividade,
        'palavras': palavras,
        'imagens': imagens,
        'sessao': sessao,
    })


@login_required
@adulto_required
@require_POST
def registrar_resposta_cartoes(request, crianca_pk, atividade_pk):
    crianca = _get_crianca_or_403(request, crianca_pk)
    atividade = _get_atividade_or_404(request, AtividadeCartoes, crianca, atividade_pk)

    try:
        body = json.loads(request.body)
    except (json.JSONDecodeError, AttributeError):
        body = request.POST

    try:
        cartao = CartaoEmocao.objects.filter(pk=body.get('cartao_id'), atividade=atividade).first()
        selecionado = CartaoEmocao.objects.filter(pk=body.get('imagem_id'), atividade=atividade).first()
    except (TypeError, ValueError):
        cartao = selecionado = None
    if not cartao or not selecionado:
        return JsonResponse({'erro': 'Cartão inválido.'}, status=400)

    try:
        tempo = float(body.get('tempo_resposta'))
    except (TypeError, ValueError):
        tempo = None

    correto = selecionado.emocao == cartao.emocao
    DesempenhoCartoes.objects.create(
        crianca=crianca,
        atividade=atividade,
        sessao=_get_sessao(body.get('sessao_id'), crianca, atividades_cartoes=atividade),
        cartao=cartao,
        cartao_selecionado=selecionado,
        correto=correto,
        tempo_resposta=tempo,
        executado_por=request.user,
    )

    return JsonResponse({'correto': correto})


# ─── Organização de Emoções em Cenários ───────────────────────────────────────

@login_required
@adulto_required
def executar_cenario(request, crianca_pk, atividade_pk):
    crianca = _get_crianca_or_403(request, crianca_pk)
    atividade = _get_atividade_or_404(request, AtividadeCenario, crianca, atividade_pk)
    sessao = _get_sessao(request.GET.get('sessao'), crianca, atividades_cenarios=atividade)

    cenarios = list(atividade.cenarios.all())
    usadas = {c.emocao_correta for c in cenarios}
    if len(cenarios) < 2 or len(usadas) < 2:
        messages.warning(request, 'Esta atividade precisa de pelo menos 2 cenários com emoções diferentes.')
        return redirect('detalhe_atividade_cenario', pk=atividade.pk)

    # Um rótulo por emoção presente; cenários e rótulos embaralhados a cada execução
    rotulos = [(valor, nome) for valor, nome in EMOCAO_CHOICES if valor in usadas]
    random.shuffle(rotulos)
    random.shuffle(cenarios)

    return render(request, 'desempenho/executar_cenarios.html', {
        'crianca': crianca,
        'atividade': atividade,
        'cenarios': cenarios,
        'rotulos': rotulos,
        'sessao': sessao,
    })


@login_required
@adulto_required
@require_POST
def registrar_resposta_cenario(request, crianca_pk, atividade_pk):
    crianca = _get_crianca_or_403(request, crianca_pk)
    atividade = _get_atividade_or_404(request, AtividadeCenario, crianca, atividade_pk)

    try:
        body = json.loads(request.body)
    except (json.JSONDecodeError, AttributeError):
        body = request.POST

    try:
        cenario = CenarioEmocao.objects.filter(pk=body.get('cenario_id'), atividade=atividade).first()
    except (TypeError, ValueError):
        cenario = None
    emocao = body.get('emocao')
    if not cenario or emocao not in dict(EMOCAO_CHOICES):
        return JsonResponse({'erro': 'Resposta inválida.'}, status=400)

    try:
        tempo = float(body.get('tempo_resposta'))
    except (TypeError, ValueError):
        tempo = None

    correto = emocao == cenario.emocao_correta
    DesempenhoCenario.objects.create(
        crianca=crianca,
        atividade=atividade,
        sessao=_get_sessao(body.get('sessao_id'), crianca, atividades_cenarios=atividade),
        cenario=cenario,
        emocao_selecionada=emocao,
        correto=correto,
        tempo_resposta=tempo,
        executado_por=request.user,
    )

    return JsonResponse({'correto': correto})


# ─── Relatórios ───────────────────────────────────────────────────────────────

@login_required
@adulto_required
def relatorio_crianca(request, crianca_pk):
    crianca = _get_crianca_or_403(request, crianca_pk)
    desempenhos = Desempenho.objects.filter(crianca=crianca).select_related(
        'atividade', 'sessao'
    ).order_by('-created_at')

    desempenhos_cartoes = DesempenhoCartoes.objects.filter(crianca=crianca).select_related(
        'atividade', 'sessao', 'cartao', 'cartao_selecionado'
    ).order_by('-created_at')

    desempenhos_cenarios = DesempenhoCenario.objects.filter(crianca=crianca).select_related(
        'atividade', 'sessao', 'cenario'
    ).order_by('-created_at')

    total = desempenhos.count() + desempenhos_cartoes.count() + desempenhos_cenarios.count()
    acertos = (
        desempenhos.filter(correto=True).count()
        + desempenhos_cartoes.filter(correto=True).count()
        + desempenhos_cenarios.filter(correto=True).count()
    )
    erros = total - acertos
    taxa = round((acertos / total * 100) if total else 0, 1)

    # Por atividade
    por_atividade = (
        desempenhos.values('atividade__titulo', 'atividade__pk')
        .annotate(total=Count('id'), acertos=Count('id', filter=Q(correto=True)))
        .order_by('atividade__titulo')
    )
    cartoes_por_atividade = (
        desempenhos_cartoes.values('atividade__titulo', 'atividade__pk')
        .annotate(total=Count('id'), acertos=Count('id', filter=Q(correto=True)))
        .order_by('atividade__titulo')
    )

    return render(request, 'desempenho/relatorio.html', {
        'crianca': crianca,
        'desempenhos': desempenhos[:30],
        'total': total,
        'acertos': acertos,
        'erros': erros,
        'taxa': taxa,
        'por_atividade': por_atividade,
        'desempenhos_cartoes': desempenhos_cartoes[:30],
        'cartoes_por_atividade': cartoes_por_atividade,
        'desempenhos_cenarios': desempenhos_cenarios[:30],
        'cenarios_por_atividade': (
            desempenhos_cenarios.values('atividade__titulo', 'atividade__pk')
            .annotate(total=Count('id'), acertos=Count('id', filter=Q(correto=True)))
            .order_by('atividade__titulo')
        ),
        'is_psicologo': request.user.role == 'psicologo',
    })


@login_required
@psicologo_required
def relatorio_geral(request):
    criancas = Crianca.objects.filter(psicologo=request.user)
    dados = []
    for c in criancas:
        total = (
            Desempenho.objects.filter(crianca=c).count()
            + DesempenhoCartoes.objects.filter(crianca=c).count()
            + DesempenhoCenario.objects.filter(crianca=c).count()
        )
        acertos = (
            Desempenho.objects.filter(crianca=c, correto=True).count()
            + DesempenhoCartoes.objects.filter(crianca=c, correto=True).count()
            + DesempenhoCenario.objects.filter(crianca=c, correto=True).count()
        )
        taxa = round((acertos / total * 100) if total else 0, 1)
        dados.append({'crianca': c, 'total': total, 'acertos': acertos, 'taxa': taxa})
    return render(request, 'desempenho/relatorio_geral.html', {'dados': dados})


# ─── Helper ───────────────────────────────────────────────────────────────────

def _get_crianca_or_403(request, crianca_pk):
    user = request.user
    if user.is_superuser or user.role == 'admin':
        return get_object_or_404(Crianca, pk=crianca_pk)
    if user.role == 'psicologo':
        return get_object_or_404(Crianca, pk=crianca_pk, psicologo=user)
    return get_object_or_404(Crianca, pk=crianca_pk, responsaveis=user)


def _get_atividade_or_404(request, model, crianca, atividade_pk):
    """Atividade de cartões ou de cenários, restrita ao que o usuário pode executar."""
    user = request.user
    if user.is_superuser or user.role == 'admin':
        return get_object_or_404(model, pk=atividade_pk)
    if user.role == 'psicologo':
        return get_object_or_404(model, pk=atividade_pk, psicologo=user)
    # responsável: só atividades de sessões em que a criança está
    return get_object_or_404(
        model.objects.distinct(), pk=atividade_pk, sessoes__criancas=crianca
    )


def _get_sessao(sessao_pk, crianca, **vinculo):
    """Sessão informada pelo cliente, aceita só se contiver a criança e a atividade."""
    if not sessao_pk:
        return None
    try:
        return Sessao.objects.filter(pk=sessao_pk, criancas=crianca, **vinculo).first()
    except (TypeError, ValueError):
        return None
