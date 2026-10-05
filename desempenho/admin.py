from django.contrib import admin
from .models import Desempenho, DesempenhoCartoes, DesempenhoCenario


@admin.register(Desempenho)
class DesempenhoAdmin(admin.ModelAdmin):
    list_display = ('crianca', 'atividade', 'sessao', 'correto', 'tempo_resposta', 'executado_por', 'created_at')
    list_filter = ('correto', 'crianca', 'atividade')
    search_fields = ('crianca__nome', 'atividade__titulo')
    date_hierarchy = 'created_at'
    readonly_fields = ('created_at',)


@admin.register(DesempenhoCartoes)
class DesempenhoCartoesAdmin(admin.ModelAdmin):
    list_display = ('crianca', 'atividade', 'sessao', 'cartao', 'correto', 'tempo_resposta', 'executado_por', 'created_at')
    list_filter = ('correto', 'crianca', 'atividade')
    search_fields = ('crianca__nome', 'atividade__titulo')
    date_hierarchy = 'created_at'
    readonly_fields = ('created_at',)


@admin.register(DesempenhoCenario)
class DesempenhoCenarioAdmin(admin.ModelAdmin):
    list_display = ('crianca', 'atividade', 'sessao', 'cenario', 'emocao_selecionada', 'correto', 'tempo_resposta', 'executado_por', 'created_at')
    list_filter = ('correto', 'crianca', 'atividade')
    search_fields = ('crianca__nome', 'atividade__titulo')
    date_hierarchy = 'created_at'
    readonly_fields = ('created_at',)
