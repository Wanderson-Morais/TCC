from django.db import models
from django.conf import settings
from criancas.models import Crianca
from atividades.models import Atividade, ImagemEmocao
from sessoes.models import Sessao


class Desempenho(models.Model):
    crianca = models.ForeignKey(Crianca, on_delete=models.CASCADE, related_name='desempenhos')
    atividade = models.ForeignKey(Atividade, on_delete=models.CASCADE, related_name='desempenhos')
    sessao = models.ForeignKey(
        Sessao, on_delete=models.SET_NULL, null=True, blank=True, related_name='desempenhos'
    )
    imagem_selecionada = models.ForeignKey(
        ImagemEmocao, on_delete=models.SET_NULL, null=True, blank=True
    )
    correto = models.BooleanField(verbose_name='Acertou')
    tempo_resposta = models.FloatField(null=True, blank=True, verbose_name='Tempo de Resposta (s)')
    executado_por = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        related_name='desempenhos_registrados',
    )
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        resultado = 'Acerto' if self.correto else 'Erro'
        return f'{self.crianca} — {self.atividade} — {resultado}'

    class Meta:
        verbose_name = 'Desempenho'
        verbose_name_plural = 'Desempenhos'
        ordering = ['-created_at']
