from django.contrib import admin
from .models import Crianca


@admin.register(Crianca)
class CriancaAdmin(admin.ModelAdmin):
    list_display = ('nome', 'data_nascimento', 'idade', 'psicologo')
    list_filter = ('psicologo',)
    search_fields = ('nome',)
    filter_horizontal = ('responsaveis',)
