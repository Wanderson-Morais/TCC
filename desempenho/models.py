from django.db import models
from django.conf import settings
from criancas.models import Crianca
from atividades.models import (
    EMOCAO_CHOICES, Atividade, AtividadeCartoes, AtividadeCenario,
    CartaoEmocao, CenarioEmocao, ImagemEmocao,
)
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


class DesempenhoCartoes(models.Model):
    """Uma tentativa de pareamento: cartão de palavra escolhido x imagem selecionada."""
    crianca = models.ForeignKey(Crianca, on_delete=models.CASCADE, related_name='desempenhos_cartoes')
    atividade = models.ForeignKey(AtividadeCartoes, on_delete=models.CASCADE, related_name='desempenhos')
    sessao = models.ForeignKey(
        Sessao, on_delete=models.SET_NULL, null=True, blank=True, related_name='desempenhos_cartoes'
    )
    cartao = models.ForeignKey(
        CartaoEmocao, on_delete=models.SET_NULL, null=True, blank=True,
        related_name='+', verbose_name='Cartão (palavra)',
    )
    cartao_selecionado = models.ForeignKey(
        CartaoEmocao, on_delete=models.SET_NULL, null=True, blank=True,
        related_name='+', verbose_name='Imagem selecionada',
    )
    correto = models.BooleanField(verbose_name='Acertou')
    tempo_resposta = models.FloatField(null=True, blank=True, verbose_name='Tempo de Resposta (s)')
    executado_por = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        related_name='desempenhos_cartoes_registrados',
    )
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        resultado = 'Acerto' if self.correto else 'Erro'
        return f'{self.crianca} — {self.atividade} — {resultado}'

    class Meta:
        verbose_name = 'Desempenho (Cartões)'
        verbose_name_plural = 'Desempenhos (Cartões)'
        ordering = ['-created_at']


class DesempenhoCenario(models.Model):
    """Uma tentativa de associação: rótulo de emoção solto sobre um cenário."""
    crianca = models.ForeignKey(Crianca, on_delete=models.CASCADE, related_name='desempenhos_cenarios')
    atividade = models.ForeignKey(AtividadeCenario, on_delete=models.CASCADE, related_name='desempenhos')
    sessao = models.ForeignKey(
        Sessao, on_delete=models.SET_NULL, null=True, blank=True, related_name='desempenhos_cenarios'
    )
    cenario = models.ForeignKey(
        CenarioEmocao, on_delete=models.SET_NULL, null=True, blank=True, related_name='+'
    )
    emocao_selecionada = models.CharField(
        max_length=20, choices=EMOCAO_CHOICES, verbose_name='Emoção selecionada'
    )
    correto = models.BooleanField(verbose_name='Acertou')
    tempo_resposta = models.FloatField(null=True, blank=True, verbose_name='Tempo de Resposta (s)')
    executado_por = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        related_name='desempenhos_cenarios_registrados',
    )
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        resultado = 'Acerto' if self.correto else 'Erro'
        return f'{self.crianca} — {self.atividade} — {resultado}'

    class Meta:
        verbose_name = 'Desempenho (Cenários)'
        verbose_name_plural = 'Desempenhos (Cenários)'
        ordering = ['-created_at']
