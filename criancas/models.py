from django.db import models
from django.conf import settings


class Crianca(models.Model):
    nome = models.CharField(max_length=100, verbose_name='Nome')
    data_nascimento = models.DateField(verbose_name='Data de Nascimento')
    foto = models.ImageField(upload_to='criancas/', blank=True, null=True, verbose_name='Foto')
    observacoes = models.TextField(blank=True, verbose_name='Observações')
    psicologo = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='criancas_psicologo',
        limit_choices_to={'role': 'psicologo'},
    )
    responsaveis = models.ManyToManyField(
        settings.AUTH_USER_MODEL,
        related_name='criancas_responsavel',
        blank=True,
        limit_choices_to={'role': 'responsavel'},
    )
    created_at = models.DateTimeField(auto_now_add=True)

    @property
    def idade(self):
        from datetime import date
        today = date.today()
        b = self.data_nascimento
        return today.year - b.year - ((today.month, today.day) < (b.month, b.day))

    def __str__(self):
        return self.nome

    class Meta:
        verbose_name = 'Criança'
        verbose_name_plural = 'Crianças'
        ordering = ['nome']
