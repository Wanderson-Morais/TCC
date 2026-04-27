from django.db import models
from django.conf import settings


EMOCAO_CHOICES = [
    ('feliz', 'Feliz'),
    ('triste', 'Triste'),
    ('raiva', 'Raiva'),
    ('medo', 'Medo'),
    ('surpresa', 'Surpresa'),
    ('nojo', 'Nojo'),
    ('neutro', 'Neutro'),
]


class Atividade(models.Model):
    titulo = models.CharField(max_length=200, verbose_name='Título')
    descricao = models.TextField(blank=True, verbose_name='Descrição')
    pergunta = models.CharField(
        max_length=300,
        verbose_name='Pergunta',
        help_text='Ex: Quem está feliz?',
    )
    emocao_correta = models.CharField(
        max_length=20,
        choices=EMOCAO_CHOICES,
        verbose_name='Emoção Correta',
    )
    psicologo = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='atividades',
        limit_choices_to={'role': 'psicologo'},
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.titulo

    class Meta:
        verbose_name = 'Atividade'
        verbose_name_plural = 'Atividades'
        ordering = ['-created_at']


class ImagemEmocao(models.Model):
    atividade = models.ForeignKey(
        Atividade, on_delete=models.CASCADE, related_name='imagens'
    )
    imagem = models.ImageField(upload_to='emocoes/', verbose_name='Imagem')
    emocao = models.CharField(max_length=20, choices=EMOCAO_CHOICES, verbose_name='Emoção')
    ordem = models.PositiveIntegerField(default=0, verbose_name='Ordem')

    @property
    def correta(self):
        return self.emocao == self.atividade.emocao_correta

    def __str__(self):
        return f'{self.get_emocao_display()} — {self.atividade.titulo}'

    class Meta:
        verbose_name = 'Imagem de Emoção'
        verbose_name_plural = 'Imagens de Emoção'
        ordering = ['ordem']
