from django.contrib.auth.models import AbstractUser
from django.db import models


class CustomUser(AbstractUser):
    ROLE_ADMIN = 'admin'
    ROLE_PSICOLOGO = 'psicologo'
    ROLE_RESPONSAVEL = 'responsavel'

    ROLE_CHOICES = [
        (ROLE_ADMIN, 'Administrador'),
        (ROLE_PSICOLOGO, 'Psicólogo'),
        (ROLE_RESPONSAVEL, 'Responsável'),
    ]

    role = models.CharField(max_length=20, choices=ROLE_CHOICES, default=ROLE_RESPONSAVEL)
    telefone = models.CharField(max_length=20, blank=True)
    crp = models.CharField(max_length=20, blank=True, verbose_name='CRP')
    aprovado = models.BooleanField(default=False, verbose_name='Aprovado pelo admin')

    def is_admin(self):
        return self.role == self.ROLE_ADMIN

    def is_psicologo(self):
        return self.role == self.ROLE_PSICOLOGO

    def is_responsavel(self):
        return self.role == self.ROLE_RESPONSAVEL

    def __str__(self):
        return f'{self.get_full_name() or self.username} ({self.get_role_display()})'

    class Meta:
        verbose_name = 'Usuário'
        verbose_name_plural = 'Usuários'
