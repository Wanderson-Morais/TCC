import json
import shutil
import tempfile
from io import BytesIO

from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase, override_settings
from django.urls import reverse
from PIL import Image

from accounts.models import CustomUser
from atividades.models import AtividadeCartoes, AtividadeCenario, CartaoEmocao, CenarioEmocao
from criancas.models import Crianca
from sessoes.models import Sessao
from .models import DesempenhoCartoes, DesempenhoCenario

MEDIA_TMP = tempfile.mkdtemp()


def _imagem(nome='rosto.png'):
    buf = BytesIO()
    Image.new('RGB', (10, 10)).save(buf, 'PNG')
    return SimpleUploadedFile(nome, buf.getvalue(), content_type='image/png')


@override_settings(MEDIA_ROOT=MEDIA_TMP)
class CartoesCorrespondentesTests(TestCase):
    @classmethod
    def tearDownClass(cls):
        super().tearDownClass()
        shutil.rmtree(MEDIA_TMP, ignore_errors=True)

    def setUp(self):
        self.psicologo = CustomUser.objects.create_user(
            'psi', password='x', role='psicologo', aprovado=True
        )
        self.outro_psicologo = CustomUser.objects.create_user(
            'psi2', password='x', role='psicologo', aprovado=True
        )
        self.responsavel = CustomUser.objects.create_user('resp', password='x', role='responsavel')
        self.crianca = Crianca.objects.create(
            nome='Ana', data_nascimento='2018-01-01', psicologo=self.psicologo
        )
        self.crianca.responsaveis.add(self.responsavel)
        self.atividade = AtividadeCartoes.objects.create(titulo='Pares', psicologo=self.psicologo)
        self.feliz = CartaoEmocao.objects.create(
            atividade=self.atividade, palavra='Feliz', imagem=_imagem(), emocao='feliz'
        )
        self.triste = CartaoEmocao.objects.create(
            atividade=self.atividade, palavra='Triste', imagem=_imagem(), emocao='triste'
        )

    def _responder(self, cartao, imagem, **extra):
        url = reverse('registrar_resposta_cartoes', args=[self.crianca.pk, self.atividade.pk])
        body = {'cartao_id': cartao.pk, 'imagem_id': imagem.pk, 'tempo_resposta': '1.50', **extra}
        return self.client.post(url, json.dumps(body), content_type='application/json')

    def test_criar_atividade_com_cartoes(self):
        self.client.force_login(self.psicologo)
        data = {
            'titulo': 'Nova', 'descricao': '',
            'cartoes-TOTAL_FORMS': '2', 'cartoes-INITIAL_FORMS': '0',
            'cartoes-MIN_NUM_FORMS': '0', 'cartoes-MAX_NUM_FORMS': '8',
            'cartoes-0-palavra': 'Medo', 'cartoes-0-emocao': 'medo', 'cartoes-0-ordem': '0',
            'cartoes-0-imagem': _imagem('a.png'),
            'cartoes-1-palavra': 'Raiva', 'cartoes-1-emocao': 'raiva', 'cartoes-1-ordem': '1',
            'cartoes-1-imagem': _imagem('b.png'),
        }
        r = self.client.post(reverse('criar_atividade_cartoes'), data)
        nova = AtividadeCartoes.objects.get(titulo='Nova')
        self.assertRedirects(r, reverse('detalhe_atividade_cartoes', args=[nova.pk]))
        self.assertEqual(nova.cartoes.count(), 2)
        self.assertEqual(nova.psicologo, self.psicologo)

    def test_criar_exige_dois_cartoes_de_emocoes_distintas(self):
        self.client.force_login(self.psicologo)
        data = {
            'titulo': 'Repetida', 'descricao': '',
            'cartoes-TOTAL_FORMS': '2', 'cartoes-INITIAL_FORMS': '0',
            'cartoes-MIN_NUM_FORMS': '0', 'cartoes-MAX_NUM_FORMS': '8',
            'cartoes-0-palavra': 'Medo', 'cartoes-0-emocao': 'medo', 'cartoes-0-ordem': '0',
            'cartoes-0-imagem': _imagem('a.png'),
            'cartoes-1-palavra': 'Assustado', 'cartoes-1-emocao': 'medo', 'cartoes-1-ordem': '1',
            'cartoes-1-imagem': _imagem('b.png'),
        }
        r = self.client.post(reverse('criar_atividade_cartoes'), data)
        self.assertEqual(r.status_code, 200)
        self.assertFalse(AtividadeCartoes.objects.filter(titulo='Repetida').exists())

    def test_executar_exibe_todos_os_cartoes(self):
        self.client.force_login(self.psicologo)
        r = self.client.get(reverse('executar_cartoes', args=[self.crianca.pk, self.atividade.pk]))
        self.assertEqual(r.status_code, 200)
        self.assertContains(r, 'Feliz')
        self.assertContains(r, 'Triste')

    def test_pareamento_correto_e_incorreto(self):
        self.client.force_login(self.psicologo)
        self.assertEqual(self._responder(self.feliz, self.triste).json(), {'correto': False})
        self.assertEqual(self._responder(self.feliz, self.feliz).json(), {'correto': True})
        acerto, erro = DesempenhoCartoes.objects.all()
        self.assertTrue(acerto.correto)
        self.assertFalse(erro.correto)
        self.assertEqual(erro.cartao_selecionado, self.triste)
        self.assertEqual(acerto.tempo_resposta, 1.5)
        self.assertEqual(acerto.executado_por, self.psicologo)

    def test_cartao_de_outra_atividade_e_rejeitado(self):
        outra = AtividadeCartoes.objects.create(titulo='Outra', psicologo=self.psicologo)
        alheio = CartaoEmocao.objects.create(
            atividade=outra, palavra='Feliz', imagem=_imagem(), emocao='feliz'
        )
        self.client.force_login(self.psicologo)
        self.assertEqual(self._responder(self.feliz, alheio).status_code, 400)
        self.assertEqual(DesempenhoCartoes.objects.count(), 0)

    def test_outro_psicologo_nao_acessa(self):
        self.client.force_login(self.outro_psicologo)
        self.assertEqual(self._responder(self.feliz, self.feliz).status_code, 404)
        r = self.client.get(reverse('detalhe_atividade_cartoes', args=[self.atividade.pk]))
        self.assertEqual(r.status_code, 404)

    def test_responsavel_so_acessa_atividade_de_sessao_da_crianca(self):
        self.client.force_login(self.responsavel)
        url = reverse('executar_cartoes', args=[self.crianca.pk, self.atividade.pk])
        self.assertEqual(self.client.get(url).status_code, 404)

        sessao = Sessao.objects.create(titulo='S1', psicologo=self.psicologo)
        sessao.criancas.add(self.crianca)
        sessao.atividades_cartoes.add(self.atividade)
        self.assertEqual(self.client.get(f'{url}?sessao={sessao.pk}').status_code, 200)

        self._responder(self.feliz, self.feliz, sessao_id=sessao.pk)
        self.assertEqual(DesempenhoCartoes.objects.get().sessao, sessao)

    def test_sessao_sem_vinculo_e_ignorada(self):
        sessao = Sessao.objects.create(titulo='Alheia', psicologo=self.outro_psicologo)
        self.client.force_login(self.psicologo)
        self._responder(self.feliz, self.feliz, sessao_id=sessao.pk)
        self.assertIsNone(DesempenhoCartoes.objects.get().sessao)

    def test_paginas_que_listam_atividades_de_cartoes(self):
        sessao = Sessao.objects.create(titulo='S1', psicologo=self.psicologo)
        sessao.criancas.add(self.crianca)
        sessao.atividades_cartoes.add(self.atividade)
        executar = reverse('executar_cartoes', args=[self.crianca.pk, self.atividade.pk])
        self.client.force_login(self.psicologo)
        for nome, args in [
            ('lista_atividades', []),
            ('detalhe_atividade_cartoes', [self.atividade.pk]),
            ('editar_atividade_cartoes', [self.atividade.pk]),
            ('excluir_atividade_cartoes', [self.atividade.pk]),
            ('criar_atividade_cartoes', []),
            ('editar_sessao', [sessao.pk]),
            ('relatorio_geral', []),
        ]:
            r = self.client.get(reverse(nome, args=args))
            self.assertEqual(r.status_code, 200, nome)
            self.assertContains(r, 'Pares') if args else None
        for nome, args in [('detalhe_sessao', [sessao.pk]), ('detalhe_crianca', [self.crianca.pk])]:
            self.assertContains(self.client.get(reverse(nome, args=args)), f'{executar}?sessao={sessao.pk}')

    def test_editar_sessao_vincula_atividade_de_cartoes(self):
        sessao = Sessao.objects.create(titulo='S1', psicologo=self.psicologo)
        self.client.force_login(self.psicologo)
        self.client.post(reverse('editar_sessao', args=[sessao.pk]), {
            'titulo': 'S1', 'descricao': '',
            'atividades_cartoes': [self.atividade.pk], 'criancas': [self.crianca.pk],
        })
        self.assertEqual(list(sessao.atividades_cartoes.all()), [self.atividade])

    def test_relatorio_soma_tentativas_de_cartoes(self):
        self.client.force_login(self.psicologo)
        self._responder(self.feliz, self.triste)
        self._responder(self.feliz, self.feliz)
        r = self.client.get(reverse('relatorio_crianca', args=[self.crianca.pk]))
        self.assertEqual(r.context['total'], 2)
        self.assertEqual(r.context['acertos'], 1)
        self.assertEqual(r.context['taxa'], 50.0)
        self.assertContains(r, 'Cartões Correspondentes')


@override_settings(MEDIA_ROOT=MEDIA_TMP)
class EmocoesEmCenariosTests(TestCase):
    def setUp(self):
        self.psicologo = CustomUser.objects.create_user(
            'psi', password='x', role='psicologo', aprovado=True
        )
        self.outro_psicologo = CustomUser.objects.create_user(
            'psi2', password='x', role='psicologo', aprovado=True
        )
        self.responsavel = CustomUser.objects.create_user('resp', password='x', role='responsavel')
        self.crianca = Crianca.objects.create(
            nome='Ana', data_nascimento='2018-01-01', psicologo=self.psicologo
        )
        self.crianca.responsaveis.add(self.responsavel)
        self.atividade = AtividadeCenario.objects.create(titulo='Cotidiano', psicologo=self.psicologo)
        self.bolo = CenarioEmocao.objects.create(
            atividade=self.atividade, imagem=_imagem(),
            descricao='Ganhou um bolo de aniversário', emocao_correta='feliz',
        )
        self.brinquedo = CenarioEmocao.objects.create(
            atividade=self.atividade, imagem=_imagem(),
            descricao='O brinquedo quebrou', emocao_correta='triste',
        )

    def _responder(self, cenario, emocao, **extra):
        url = reverse('registrar_resposta_cenario', args=[self.crianca.pk, self.atividade.pk])
        body = {'cenario_id': cenario.pk, 'emocao': emocao, 'tempo_resposta': '2.25', **extra}
        return self.client.post(url, json.dumps(body), content_type='application/json')

    def _dados_formset(self, emocao_0, emocao_1):
        return {
            'titulo': 'Nova', 'descricao': '',
            'cenarios-TOTAL_FORMS': '2', 'cenarios-INITIAL_FORMS': '0',
            'cenarios-MIN_NUM_FORMS': '0', 'cenarios-MAX_NUM_FORMS': '8',
            'cenarios-0-descricao': 'Viu um cachorro bravo', 'cenarios-0-emocao_correta': emocao_0,
            'cenarios-0-ordem': '0', 'cenarios-0-imagem': _imagem('a.png'),
            'cenarios-1-descricao': 'Ganhou um presente', 'cenarios-1-emocao_correta': emocao_1,
            'cenarios-1-ordem': '1', 'cenarios-1-imagem': _imagem('b.png'),
        }

    def test_criar_atividade_com_cenarios(self):
        self.client.force_login(self.psicologo)
        r = self.client.post(reverse('criar_atividade_cenario'), self._dados_formset('medo', 'feliz'))
        nova = AtividadeCenario.objects.get(titulo='Nova')
        self.assertRedirects(r, reverse('detalhe_atividade_cenario', args=[nova.pk]))
        self.assertEqual(nova.cenarios.count(), 2)
        self.assertEqual(nova.psicologo, self.psicologo)

    def test_criar_exige_emocoes_diferentes(self):
        self.client.force_login(self.psicologo)
        r = self.client.post(reverse('criar_atividade_cenario'), self._dados_formset('medo', 'medo'))
        self.assertEqual(r.status_code, 200)
        self.assertFalse(AtividadeCenario.objects.filter(titulo='Nova').exists())

    def test_executar_exibe_cenarios_e_um_rotulo_por_emocao(self):
        CenarioEmocao.objects.create(
            atividade=self.atividade, imagem=_imagem(),
            descricao='Passeio no parque', emocao_correta='feliz',
        )
        self.client.force_login(self.psicologo)
        r = self.client.get(reverse('executar_cenario', args=[self.crianca.pk, self.atividade.pk]))
        self.assertEqual(r.status_code, 200)
        self.assertEqual(len(r.context['cenarios']), 3)
        self.assertEqual(sorted(v for v, _ in r.context['rotulos']), ['feliz', 'triste'])

    def test_associacao_correta_e_incorreta(self):
        self.client.force_login(self.psicologo)
        self.assertEqual(self._responder(self.bolo, 'triste').json(), {'correto': False})
        self.assertEqual(self._responder(self.bolo, 'feliz').json(), {'correto': True})
        erro, acerto = DesempenhoCenario.objects.order_by('id')
        self.assertTrue(acerto.correto)
        self.assertFalse(erro.correto)
        self.assertEqual(erro.emocao_selecionada, 'triste')
        self.assertEqual(acerto.cenario, self.bolo)
        self.assertEqual(acerto.tempo_resposta, 2.25)

    def test_resposta_invalida_e_rejeitada(self):
        outra = AtividadeCenario.objects.create(titulo='Outra', psicologo=self.psicologo)
        alheio = CenarioEmocao.objects.create(
            atividade=outra, imagem=_imagem(), descricao='x', emocao_correta='feliz'
        )
        self.client.force_login(self.psicologo)
        self.assertEqual(self._responder(alheio, 'feliz').status_code, 400)
        self.assertEqual(self._responder(self.bolo, 'inexistente').status_code, 400)
        self.assertEqual(DesempenhoCenario.objects.count(), 0)

    def test_outro_psicologo_nao_acessa(self):
        self.client.force_login(self.outro_psicologo)
        self.assertEqual(self._responder(self.bolo, 'feliz').status_code, 404)
        r = self.client.get(reverse('detalhe_atividade_cenario', args=[self.atividade.pk]))
        self.assertEqual(r.status_code, 404)

    def test_responsavel_so_acessa_atividade_de_sessao_da_crianca(self):
        self.client.force_login(self.responsavel)
        url = reverse('executar_cenario', args=[self.crianca.pk, self.atividade.pk])
        self.assertEqual(self.client.get(url).status_code, 404)

        sessao = Sessao.objects.create(titulo='S1', psicologo=self.psicologo)
        sessao.criancas.add(self.crianca)
        sessao.atividades_cenarios.add(self.atividade)
        self.assertEqual(self.client.get(f'{url}?sessao={sessao.pk}').status_code, 200)

        self._responder(self.bolo, 'feliz', sessao_id=sessao.pk)
        self.assertEqual(DesempenhoCenario.objects.get().sessao, sessao)

    def test_paginas_e_relatorio(self):
        sessao = Sessao.objects.create(titulo='S1', psicologo=self.psicologo)
        self.client.force_login(self.psicologo)
        self.client.post(reverse('editar_sessao', args=[sessao.pk]), {
            'titulo': 'S1', 'descricao': '',
            'atividades_cenarios': [self.atividade.pk], 'criancas': [self.crianca.pk],
        })
        self.assertEqual(list(sessao.atividades_cenarios.all()), [self.atividade])

        self._responder(self.bolo, 'triste')
        self._responder(self.bolo, 'feliz')

        for nome, args in [
            ('lista_atividades', []),
            ('detalhe_atividade_cenario', [self.atividade.pk]),
            ('editar_atividade_cenario', [self.atividade.pk]),
            ('excluir_atividade_cenario', [self.atividade.pk]),
            ('criar_atividade_cenario', []),
            ('relatorio_geral', []),
        ]:
            self.assertEqual(self.client.get(reverse(nome, args=args)).status_code, 200, nome)

        executar = reverse('executar_cenario', args=[self.crianca.pk, self.atividade.pk])
        for nome, args in [('detalhe_sessao', [sessao.pk]), ('detalhe_crianca', [self.crianca.pk])]:
            self.assertContains(self.client.get(reverse(nome, args=args)), f'{executar}?sessao={sessao.pk}')

        r = self.client.get(reverse('relatorio_crianca', args=[self.crianca.pk]))
        self.assertEqual((r.context['total'], r.context['acertos'], r.context['taxa']), (2, 1, 50.0))
        self.assertContains(r, 'Emoções em Cenários')
        self.assertContains(r, 'Ganhou um bolo')
