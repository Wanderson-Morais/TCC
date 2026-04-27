from django.contrib import admin
from .models import Atividade, ImagemEmocao


class ImagemEmocaoInline(admin.TabularInline):
    model = ImagemEmocao
    extra = 2


@admin.register(Atividade)
class AtividadeAdmin(admin.ModelAdmin):
    list_display = ('titulo', 'pergunta', 'emocao_correta', 'psicologo', 'created_at')
    list_filter = ('emocao_correta', 'psicologo')
    search_fields = ('titulo',)
    inlines = [ImagemEmocaoInline]
