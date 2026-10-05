from django.contrib import admin
from .models import (
    Atividade, AtividadeCartoes, AtividadeCenario, CartaoEmocao, CenarioEmocao, ImagemEmocao,
)


class ImagemEmocaoInline(admin.TabularInline):
    model = ImagemEmocao
    extra = 2


@admin.register(Atividade)
class AtividadeAdmin(admin.ModelAdmin):
    list_display = ('titulo', 'pergunta', 'emocao_correta', 'psicologo', 'created_at')
    list_filter = ('emocao_correta', 'psicologo')
    search_fields = ('titulo',)
    inlines = [ImagemEmocaoInline]


class CartaoEmocaoInline(admin.TabularInline):
    model = CartaoEmocao
    extra = 2


@admin.register(AtividadeCartoes)
class AtividadeCartoesAdmin(admin.ModelAdmin):
    list_display = ('titulo', 'psicologo', 'created_at')
    list_filter = ('psicologo',)
    search_fields = ('titulo',)
    inlines = [CartaoEmocaoInline]


class CenarioEmocaoInline(admin.TabularInline):
    model = CenarioEmocao
    extra = 2


@admin.register(AtividadeCenario)
class AtividadeCenarioAdmin(admin.ModelAdmin):
    list_display = ('titulo', 'psicologo', 'created_at')
    list_filter = ('psicologo',)
    search_fields = ('titulo',)
    inlines = [CenarioEmocaoInline]
