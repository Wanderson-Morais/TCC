import json
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.views.decorators.http import require_POST
from django.contrib import messages
from django.db.models import Count, Q
from .models import Desempenho
from atividades.models import Atividade, ImagemEmocao
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


# ─── Relatórios ───────────────────────────────────────────────────────────────

@login_required
@adulto_required
def relatorio_crianca(request, crianca_pk):
    crianca = _get_crianca_or_403(request, crianca_pk)
    desempenhos = Desempenho.objects.filter(crianca=crianca).select_related(
        'atividade', 'sessao'
    ).order_by('-created_at')

    total = desempenhos.count()
    acertos = desempenhos.filter(correto=True).count()
    erros = total - acertos
    taxa = round((acertos / total * 100) if total else 0, 1)

    # Por atividade
    por_atividade = (
        desempenhos.values('atividade__titulo', 'atividade__pk')
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
        'is_psicologo': request.user.role == 'psicologo',
    })


@login_required
@psicologo_required
def relatorio_geral(request):
    criancas = Crianca.objects.filter(psicologo=request.user)
    dados = []
    for c in criancas:
        total = Desempenho.objects.filter(crianca=c).count()
        acertos = Desempenho.objects.filter(crianca=c, correto=True).count()
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
