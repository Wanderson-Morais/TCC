from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import CustomUser


@admin.register(CustomUser)
class CustomUserAdmin(UserAdmin):
    list_display = ('username', 'get_full_name', 'email', 'role', 'aprovado', 'is_active')
    list_filter = ('role', 'aprovado', 'is_active')
    search_fields = ('username', 'first_name', 'last_name', 'email')
    fieldsets = UserAdmin.fieldsets + (
        ('Perfil EmoTEA', {'fields': ('role', 'telefone', 'crp', 'aprovado')}),
    )
    add_fieldsets = UserAdmin.add_fieldsets + (
        ('Perfil EmoTEA', {'fields': ('role', 'telefone', 'crp', 'aprovado')}),
    )
    actions = ['aprovar_psicologos']

    def aprovar_psicologos(self, request, queryset):
        queryset.filter(role='psicologo').update(aprovado=True)
        self.message_user(request, 'Psicólogos aprovados.')
    aprovar_psicologos.short_description = 'Aprovar psicólogos selecionados'
