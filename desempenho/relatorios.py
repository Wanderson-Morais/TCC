"""Cálculos dos relatórios: junta as respostas dos três tipos de atividade."""
from collections import defaultdict
from datetime import timedelta

from django.db.models import Max
from django.utils import timezone

from .models import Desempenho, DesempenhoCartoes, DesempenhoCenario

PERIODOS = [
    ('7', 'Últimos 7 dias'),
    ('30', 'Últimos 30 dias'),
    ('tudo', 'Desde o início'),
]
PERIODO_PADRAO = '30'

TIPOS = {
    'imagens': {
        'label': 'Imagens', 'ordem': 0,
        'executar': 'executar_atividade', 'detalhe': 'detalhe_atividade',
    },
    'cartoes': {
        'label': 'Cartões Correspondentes', 'ordem': 1,
        'executar': 'executar_cartoes', 'detalhe': 'detalhe_atividade_cartoes',
    },
    'cenarios': {
        'label': 'Emoções em Cenários', 'ordem': 2,
        'executar': 'executar_cenario', 'detalhe': 'detalhe_atividade_cenario',
    },
}

# Mesmas faixas usadas nas barras de progresso: >= 70 verde, < 40 vermelho
SITUACOES = {
    'apoio': {'label': 'Precisa de apoio', 'icone': '✖', 'badge': 'badge-danger'},
    'atencao': {'label': 'Atenção', 'icone': '⚠', 'badge': 'badge-warning'},
    'bem': {'label': 'Indo bem', 'icone': '✔', 'badge': 'badge-success'},
    'sem': {'label': 'Sem dados', 'icone': '—', 'badge': 'badge-muted'},
}


def periodo_da_request(request):
    periodo = request.GET.get('periodo')
    return periodo if periodo in dict(PERIODOS) else PERIODO_PADRAO


def inicio_do_periodo(periodo):
    """Data a partir da qual as respostas contam; None para "desde o início"."""
    if periodo == 'tudo':
        return None
    return timezone.now() - timedelta(days=int(periodo))


def respostas(criancas, desde=None):
    """Respostas das atividades de imagens, cartões e cenários num formato único."""
    filtro = {'crianca__in': criancas}
    if desde:
        filtro['created_at__gte'] = desde
    comuns = ('crianca_id', 'correto', 'tempo_resposta', 'sessao_id', 'atividade_id', 'atividade__titulo')

    lista = []
    for tipo, model in (('imagens', Desempenho), ('cartoes', DesempenhoCartoes), ('cenarios', DesempenhoCenario)):
        lista.extend(_resposta(r, tipo) for r in model.objects.filter(**filtro).values(*comuns))
    return lista


def _resposta(r, tipo):
    return {
        'crianca_id': r['crianca_id'],
        'correto': r['correto'],
        'tempo': r['tempo_resposta'],
        'sessao_id': r['sessao_id'],
        'tipo': tipo,
        'atividade_id': r['atividade_id'],
        'atividade': r['atividade__titulo'],
    }


def ultima_atividade(criancas):
    """Data da resposta mais recente de cada criança, em todo o histórico."""
    ultimas = {}
    for model in (Desempenho, DesempenhoCartoes, DesempenhoCenario):
        for r in model.objects.filter(crianca__in=criancas).values('crianca_id').annotate(ultima=Max('created_at')):
            atual = ultimas.get(r['crianca_id'])
            if not atual or r['ultima'] > atual:
                ultimas[r['crianca_id']] = r['ultima']
    return ultimas


def taxa(acertos, total):
    return round(acertos / total * 100, 1) if total else 0


def contar(lista):
    total = len(lista)
    acertos = sum(1 for r in lista if r['correto'])
    return total, acertos, taxa(acertos, total)


def situacao(taxa_acerto, total):
    if not total:
        return 'sem'
    return 'bem' if taxa_acerto >= 70 else 'atencao' if taxa_acerto >= 40 else 'apoio'


def classe_barra(taxa_acerto):
    return 'success' if taxa_acerto >= 70 else 'danger' if taxa_acerto < 40 else ''


def ultima_txt(data):
    if not data:
        return 'Nenhuma ainda'
    dias = (timezone.localdate() - timezone.localdate(data)).days
    return 'Hoje' if dias <= 0 else 'Ontem' if dias == 1 else f'Há {dias} dias'


def por_atividade(lista):
    grupos = defaultdict(list)
    for r in lista:
        grupos[(r['tipo'], r['atividade_id'])].append(r)
    linhas = []
    for (tipo, atividade_id), itens in grupos.items():
        total, acertos, t = contar(itens)
        linhas.append({
            'tipo': tipo, 'tipo_label': TIPOS[tipo]['label'],
            'url_executar': TIPOS[tipo]['executar'], 'url_detalhe': TIPOS[tipo]['detalhe'],
            'pk': atividade_id, 'titulo': itens[0]['atividade'],
            'total': total, 'acertos': acertos, 'pct': round(t), 'barra': classe_barra(t),
        })
    linhas.sort(key=lambda a: (TIPOS[a['tipo']]['ordem'], a['titulo']))
    return linhas
