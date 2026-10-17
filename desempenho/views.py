import json
import random
from django.shortcuts import render, redirect, get_object_or_404
from django.urls import reverse
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.views.decorators.http import require_POST
from django.contrib import messages
from .models import Desempenho, DesempenhoCartoes, DesempenhoCenario
from atividades.models import (
    EMOCAO_CHOICES, Atividade, AtividadeCartoes, AtividadeCenario,
    CartaoEmocao, CenarioEmocao, ImagemEmocao,
)
from criancas.models import Crianca
from sessoes.models import Sessao
from accounts.decorators import adulto_required, psicologo_required
from . import relatorios as rel


# ─── Execução de Atividade ────────────────────────────────────────────────────

@login_required
@adulto_required
def executar_atividade(request, crianca_pk, atividade_pk):
    crianca = _get_crianca_or_403(request, crianca_pk)
    atividade = get_object_or_404(Atividade, pk=atividade_pk)
    sessao = _get_sessao(request.GET.get('sessao'), crianca, atividades=atividade)

    imagens = list(atividade.imagens.all())
    if not imagens:
        messages.warning(request, 'Esta atividade não possui imagens cadastradas.')
        return redirect('detalhe_atividade', pk=atividade.pk)

    return render(request, 'desempenho/executar.html', {
        'crianca': crianca,
        'atividade': atividade,
        'imagens': imagens,
        'sessao': sessao,
        **_progresso_sessao(sessao, crianca, 'executar_atividade', atividade.pk),
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
        **_progresso_sessao(sessao, crianca, 'executar_cartoes', atividade.pk),
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

    # Cada cena é uma atividade: a página mostra só a cena pedida em ?cena=
    cena = request.GET.get('cena', '')
    cenario = next((c for c in cenarios if str(c.pk) == cena), cenarios[0])
    pos = cenarios.index(cenario)

    # Um rótulo por emoção presente na atividade, embaralhados a cada cena
    rotulos = [(valor, nome) for valor, nome in EMOCAO_CHOICES if valor in usadas]
    random.shuffle(rotulos)

    progresso = _progresso_sessao(sessao, crianca, 'executar_cenario', atividade.pk, cenario.pk)
    texto_proxima = None
    if progresso['indice_atual'] is None and pos + 1 < len(cenarios):
        # Fora de uma sessão: segue para a próxima cena da mesma atividade
        progresso['proxima_url'] = (
            reverse('executar_cenario', args=[crianca.pk, atividade.pk])
            + f'?cena={cenarios[pos + 1].pk}' + (f'&sessao={sessao.pk}' if sessao else '')
        )
        texto_proxima = 'Próxima cena →'

    return render(request, 'desempenho/executar_cenarios.html', {
        'crianca': crianca,
        'atividade': atividade,
        'cenario': cenario,
        'cena_numero': pos + 1,
        'total_cenas': len(cenarios),
        'rotulos': rotulos,
        'sessao': sessao,
        'texto_proxima': texto_proxima,
        **progresso,
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

    return JsonResponse({'correto': correto, 'emocao_correta': cenario.emocao_correta})


# ─── Relatórios ───────────────────────────────────────────────────────────────

@login_required
@adulto_required
def relatorio_crianca(request, crianca_pk):
    crianca = _get_crianca_or_403(request, crianca_pk)
    periodo = rel.periodo_da_request(request)
    atuais = rel.respostas([crianca], desde=rel.inicio_do_periodo(periodo))

    total, acertos, taxa = rel.contar(atuais)
    tempos = [r['tempo'] for r in atuais if r['tempo'] is not None]
    situacao = rel.situacao(taxa, total)

    aba = request.GET.get('aba')
    pode_ver_geral = request.user.is_superuser or request.user.role == 'psicologo'

    return render(request, 'desempenho/relatorio.html', {
        'crianca': crianca,
        'periodo': periodo,
        'periodos': rel.PERIODOS,
        'periodo_label': dict(rel.PERIODOS)[periodo],
        'aba': aba if aba in ('resumo', 'atividade') else 'resumo',
        'total': total,
        'acertos': acertos,
        'erros': total - acertos,
        'taxa': taxa,
        'taxa_pct': round(taxa),
        'situacao': rel.SITUACOES[situacao],
        'tempo_medio': sum(tempos) / len(tempos) if tempos else None,
        'sessoes': len({r['sessao_id'] for r in atuais if r['sessao_id']}),
        'por_atividade': rel.por_atividade(atuais),
        'ultima': rel.ultima_txt(rel.ultima_atividade([crianca]).get(crianca.pk)),
        'sessao_inicio': crianca.sessoes.order_by('-data_sessao', '-created_at').first(),
        'is_psicologo': request.user.role == 'psicologo',
        'pode_ver_geral': pode_ver_geral,
    })


@login_required
@psicologo_required
def relatorio_geral(request):
    periodo = rel.periodo_da_request(request)
    criancas = list(Crianca.objects.filter(psicologo=request.user).prefetch_related('sessoes'))
    todas = rel.respostas(criancas, desde=rel.inicio_do_periodo(periodo))
    ultimas = rel.ultima_atividade(criancas)

    por_crianca = {c.pk: [] for c in criancas}
    for r in todas:
        por_crianca[r['crianca_id']].append(r)

    dados = []
    for c in criancas:
        total, acertos, taxa = rel.contar(por_crianca[c.pk])
        sessoes = sorted(c.sessoes.all(), key=lambda s: s.created_at, reverse=True)
        dados.append({
            'crianca': c, 'total': total, 'acertos': acertos,
            'taxa': taxa, 'taxa_pct': round(taxa), 'barra': rel.classe_barra(taxa),
            'ultima': ultimas.get(c.pk), 'ultima_txt': rel.ultima_txt(ultimas.get(c.pk)),
            'sessao_inicio': sessoes[0] if sessoes else None,
        })

    com_dados = [d for d in dados if d['total']]
    resumo = {
        'criancas': len(dados),
        'respostas': sum(d['total'] for d in dados),
        'media': round(sum(d['taxa'] for d in com_dados) / len(com_dados)) if com_dados else 0,
    }

    # Busca e ordem vindas da URL
    busca = request.GET.get('q', '').strip()
    ordem = request.GET.get('ordem', 'acertos')
    lista = [d for d in dados if busca.lower() in d['crianca'].nome.lower()]
    if ordem == 'nome':
        lista.sort(key=lambda d: d['crianca'].nome.lower())
    elif ordem == 'recente':
        lista.sort(key=lambda d: d['ultima'].timestamp() if d['ultima'] else 0, reverse=True)
    else:
        ordem = 'acertos'
        # Menor taxa de acerto primeiro; quem ainda não respondeu vai para o fim
        lista.sort(key=lambda d: (not d['total'], d['taxa']))

    def url_com(**mudancas):
        params = request.GET.copy()
        for chave, valor in mudancas.items():
            params[chave] = valor
        return f'?{params.urlencode()}'

    return render(request, 'desempenho/relatorio_geral.html', {
        'dados': lista,
        'tem_criancas': bool(dados),
        'resumo': resumo,
        'periodo': periodo,
        'periodos': [(p, l, url_com(periodo=p)) for p, l in rel.PERIODOS],
        'busca': busca,
        'ordem': ordem,
    })


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


# ─── Reprodução de sessão ─────────────────────────────────────────────────────

# Tipo de atividade de cada tela de execução (define a cor da tela e da barra da sessão)
TIPO_POR_TELA = {
    'executar_atividade': 'imagens',
    'executar_cartoes': 'cartoes',
    'executar_cenario': 'cenarios',
}


def sequencia_sessao(sessao):
    """Todas as atividades da sessão na ordem de reprodução, como (url_name, pk, cena).

    Primeiro as atividades de imagens (pela ordem definida na sessão), depois
    as de cartões e por fim as de cenários. Cada cena de uma atividade de
    cenários conta como uma atividade; nos outros tipos, cena é None.
    """
    passos = (
        [('executar_atividade', pk, None) for pk in
         sessao.atividades.order_by('sessaoatividade__ordem', 'titulo').values_list('pk', flat=True)]
        + [('executar_cartoes', pk, None) for pk in
           sessao.atividades_cartoes.order_by('titulo', 'pk').values_list('pk', flat=True)]
    )
    for atividade in sessao.atividades_cenarios.order_by('titulo', 'pk').prefetch_related('cenarios'):
        passos += [('executar_cenario', atividade.pk, c.pk) for c in atividade.cenarios.all()]
    return passos


def url_execucao(passo, crianca, sessao):
    url_name, atividade_pk, cena = passo
    return reverse(url_name, kwargs={
        'crianca_pk': crianca.pk, 'atividade_pk': atividade_pk,
    }) + f'?sessao={sessao.pk}' + (f'&cena={cena}' if cena else '')


def _progresso_sessao(sessao, crianca, url_name, atividade_pk, cena=None):
    """Posição da atividade na sessão e URL da próxima, para a tela de execução."""
    vazio = {'proxima_url': None, 'indice_atual': None, 'total_atividades': None}
    if not sessao:
        return vazio
    passos = sequencia_sessao(sessao)
    try:
        pos = passos.index((url_name, atividade_pk, cena))
    except ValueError:
        return vazio
    return {
        'proxima_url': url_execucao(passos[pos + 1], crianca, sessao) if pos + 1 < len(passos) else None,
        'indice_atual': pos + 1,
        'total_atividades': len(passos),
        'restam': len(passos) - pos - 1,
        # Um segmento por atividade na barra de progresso, com a cor do tipo de cada uma
        'segmentos': [
            {'estado': 'feito' if i < pos else 'atual' if i == pos else '', 'tipo': TIPO_POR_TELA[passo[0]]}
            for i, passo in enumerate(passos)
        ],
    }
