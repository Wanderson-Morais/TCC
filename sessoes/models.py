from django.db import models
from django.conf import settings
from atividades.models import Atividade
from criancas.models import Crianca


class Sessao(models.Model):
    titulo = models.CharField(max_length=200, verbose_name='Título')
    descricao = models.TextField(blank=True, verbose_name='Descrição')
    data_sessao = models.DateField(null=True, blank=True, verbose_name='Data da Sessão')
    psicologo = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='sessoes',
        limit_choices_to={'role': 'psicologo'},
    )
    atividades = models.ManyToManyField(
        Atividade,
        through='SessaoAtividade',
        related_name='sessoes',
        blank=True,
    )
    criancas = models.ManyToManyField(
        Crianca,
        through='SessaoCrianca',
        related_name='sessoes',
        blank=True,
    )
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.titulo

    class Meta:
        verbose_name = 'Sessão'
        verbose_name_plural = 'Sessões'
        ordering = ['-created_at']


class SessaoAtividade(models.Model):
    sessao = models.ForeignKey(Sessao, on_delete=models.CASCADE)
    atividade = models.ForeignKey(Atividade, on_delete=models.CASCADE)
    ordem = models.PositiveIntegerField(default=0)

    class Meta:
        ordering = ['ordem']
        unique_together = ('sessao', 'atividade')


class SessaoCrianca(models.Model):
    sessao = models.ForeignKey(Sessao, on_delete=models.CASCADE)
    crianca = models.ForeignKey(Crianca, on_delete=models.CASCADE)

    class Meta:
        unique_together = ('sessao', 'crianca')
