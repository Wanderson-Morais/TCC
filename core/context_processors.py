from django.conf import settings

# Arquivos cujo conteúdo muda com frequência durante o desenvolvimento
ARQUIVOS_VERSIONADOS = ('css/style.css', 'js/main.js')


def versao_static(request):
    """Número que muda quando style.css ou main.js mudam.

    Vai no fim da URL (?v=...) para o navegador baixar a versão nova em vez de
    usar a que guardou em cache.
    """
    versao = 0
    for pasta in settings.STATICFILES_DIRS:
        for nome in ARQUIVOS_VERSIONADOS:
            try:
                versao = max(versao, int((pasta / nome).stat().st_mtime))
            except OSError:
                pass
    return {'versao_static': versao}
