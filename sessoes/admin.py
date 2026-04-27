from django.contrib import admin
from .models import Sessao, SessaoAtividade, SessaoCrianca


class SessaoAtividadeInline(admin.TabularInline):
    model = SessaoAtividade
    extra = 1


class SessaoCriancaInline(admin.TabularInline):
    model = SessaoCrianca
    extra = 1


@admin.register(Sessao)
class SessaoAdmin(admin.ModelAdmin):
    list_display = ('titulo', 'psicologo', 'data_sessao', 'created_at')
    list_filter = ('psicologo',)
    search_fields = ('titulo',)
    inlines = [SessaoAtividadeInline, SessaoCriancaInline]
