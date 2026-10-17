import json
import shutil
import tempfile
from datetime import timedelta
from io import BytesIO

from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase, override_settings
from django.urls import reverse
from django.utils import timezone
from PIL import Image

from accounts.models import CustomUser
from atividades.models import (
    Atividade, AtividadeCartoes, AtividadeCenario, CartaoEmocao, CenarioEmocao, ImagemEmocao,
)
from criancas.models import Crianca
from sessoes.models import Sessao, SessaoAtividade
from .models import Desempenho, DesempenhoCartoes, DesempenhoCenario

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
        url = reverse('executar_cenario', args=[self.crianca.pk, self.atividade.pk])
        r = self.client.get(url)
        self.assertEqual(r.status_code, 200)
        self.assertEqual(r.context['cenario'], self.bolo)
        self.assertEqual((r.context['cena_numero'], r.context['total_cenas']), (1, 3))
        self.assertEqual(sorted(v for v, _ in r.context['rotulos']), ['feliz', 'triste'])
        self.assertEqual(r.context['proxima_url'], f'{url}?cena={self.brinquedo.pk}')
        self.assertContains(r, 'Próxima cena →')
        self.assertNotContains(r, 'O brinquedo quebrou')

        ultima = self.atividade.cenarios.last()
        r = self.client.get(f'{url}?cena={ultima.pk}')
        self.assertEqual(r.context['cenario'], ultima)
        self.assertIsNone(r.context['proxima_url'])
        self.assertContains(r, 'Continuar →')

    def test_associacao_correta_e_incorreta(self):
        self.client.force_login(self.psicologo)
        self.assertEqual(self._responder(self.bolo, 'triste').json(), {'correto': False, 'emocao_correta': 'feliz'})
        self.assertEqual(self._responder(self.bolo, 'feliz').json(), {'correto': True, 'emocao_correta': 'feliz'})
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
        self.assertContains(r, 'Cotidiano')


@override_settings(MEDIA_ROOT=MEDIA_TMP)
class ReproducaoSessaoTests(TestCase):
    def setUp(self):
        self.psicologo = CustomUser.objects.create_user(
            'psi', password='x', role='psicologo', aprovado=True
        )
        self.responsavel = CustomUser.objects.create_user('resp', password='x', role='responsavel')
        self.ana = Crianca.objects.create(nome='Ana', data_nascimento='2018-01-01', psicologo=self.psicologo)
        self.ana.responsaveis.add(self.responsavel)
        self.bia = Crianca.objects.create(nome='Bia', data_nascimento='2018-01-01', psicologo=self.psicologo)

        self.imagens = Atividade.objects.create(
            titulo='Quem está feliz', pergunta='Quem está feliz?', emocao_correta='feliz',
            psicologo=self.psicologo,
        )
        ImagemEmocao.objects.create(atividade=self.imagens, imagem=_imagem(), emocao='feliz')
        self.cartoes = AtividadeCartoes.objects.create(titulo='Pares', psicologo=self.psicologo)
        for emocao in ('feliz', 'triste'):
            CartaoEmocao.objects.create(atividade=self.cartoes, palavra=emocao, imagem=_imagem(), emocao=emocao)
        self.cenarios = AtividadeCenario.objects.create(titulo='Cenas', psicologo=self.psicologo)
        for emocao in ('feliz', 'triste'):
            CenarioEmocao.objects.create(
                atividade=self.cenarios, imagem=_imagem(), descricao=emocao, emocao_correta=emocao
            )

        self.sessao = Sessao.objects.create(titulo='Sessão 1', psicologo=self.psicologo)
        SessaoAtividade.objects.create(sessao=self.sessao, atividade=self.imagens, ordem=0)
        self.sessao.atividades_cartoes.add(self.cartoes)
        self.sessao.atividades_cenarios.add(self.cenarios)
        self.sessao.criancas.add(self.ana, self.bia)
        self.sufixo = f'?sessao={self.sessao.pk}'

    def test_iniciar_abre_primeira_atividade(self):
        self.client.force_login(self.psicologo)
        r = self.client.get(reverse('iniciar_sessao', args=[self.sessao.pk]) + f'?crianca={self.bia.pk}')
        self.assertRedirects(
            r, reverse('executar_atividade', args=[self.bia.pk, self.imagens.pk]) + self.sufixo
        )

    def test_iniciar_sem_crianca_com_varias_volta_ao_detalhe(self):
        self.client.force_login(self.psicologo)
        r = self.client.get(reverse('iniciar_sessao', args=[self.sessao.pk]))
        self.assertRedirects(r, reverse('detalhe_sessao', args=[self.sessao.pk]))

    def test_sequencia_passa_por_todos_os_tipos(self):
        self.client.force_login(self.psicologo)
        r = self.client.get(reverse('executar_atividade', args=[self.ana.pk, self.imagens.pk]) + self.sufixo)
        self.assertEqual(r.context['indice_atual'], 1)
        # Cada cena de cenários conta como uma atividade: 1 + 1 + 2 cenas
        self.assertEqual(r.context['total_atividades'], 4)
        self.assertEqual(
            r.context['proxima_url'],
            reverse('executar_cartoes', args=[self.ana.pk, self.cartoes.pk]) + self.sufixo,
        )

        r = self.client.get(reverse('executar_cartoes', args=[self.ana.pk, self.cartoes.pk]) + self.sufixo)
        self.assertContains(r, 'class="sidebar"')
        self.assertContains(r, 'Faltam 2')
        self.assertContains(r, 'Próxima atividade →')
        url_cenario = reverse('executar_cenario', args=[self.ana.pk, self.cenarios.pk]) + self.sufixo
        primeira, segunda = self.cenarios.cenarios.all()
        self.assertEqual(r.context['proxima_url'], f'{url_cenario}&cena={primeira.pk}')

        r = self.client.get(f'{url_cenario}&cena={primeira.pk}')
        self.assertEqual(r.context['indice_atual'], 3)
        self.assertEqual(r.context['cenario'], primeira)
        self.assertEqual(r.context['proxima_url'], f'{url_cenario}&cena={segunda.pk}')

        r = self.client.get(f'{url_cenario}&cena={segunda.pk}')
        self.assertEqual(r.context['indice_atual'], 4)
        self.assertEqual(r.context['cenario'], segunda)
        self.assertIsNone(r.context['proxima_url'])
        # Última atividade: mesma tela com barra lateral, "Terminar" e a tela de parabéns
        self.assertContains(r, 'class="sidebar"')
        self.assertContains(r, 'Última atividade!')
        self.assertContains(r, 'Terminar ✔')
        self.assertContains(r, 'Parabéns, Ana!')

    def test_tela_de_execucao_com_barra_lateral_e_progresso(self):
        self.client.force_login(self.psicologo)
        url = reverse('executar_atividade', args=[self.ana.pk, self.imagens.pk])
        r = self.client.get(url + self.sufixo)
        self.assertContains(r, 'class="sidebar"')
        self.assertContains(r, 'js/main.js?v=')  # força o navegador a baixar o JS novo
        self.assertContains(r, 'Faltam 3')
        self.assertContains(r, '✖ Sair')
        self.assertContains(r, reverse('detalhe_sessao', args=[self.sessao.pk]))
        self.assertContains(r, 'Próxima atividade →')
        self.assertEqual(
            [(s['estado'], s['tipo']) for s in r.context['segmentos']],
            [('atual', 'imagens'), ('', 'cartoes'), ('', 'cenarios'), ('', 'cenarios')],
        )
        self.assertContains(r, 'exec-area tipo-imagens')
        self.assertContains(r, '🖼️ Imagens')

        # Fora de uma sessão: sem barra de progresso e sem tela de parabéns
        r = self.client.get(url)
        self.assertNotContains(r, 'exec-segmentos')
        self.assertNotContains(r, 'Parabéns')
        self.assertContains(r, 'Continuar →')

    def test_responsavel_so_inicia_com_a_propria_crianca(self):
        self.client.force_login(self.responsavel)
        url = reverse('iniciar_sessao', args=[self.sessao.pk])
        r = self.client.get(url + f'?crianca={self.bia.pk}')
        self.assertRedirects(r, reverse('detalhe_sessao', args=[self.sessao.pk]))
        r = self.client.get(url)  # só uma criança visível: inicia direto
        self.assertRedirects(
            r, reverse('executar_atividade', args=[self.ana.pk, self.imagens.pk]) + self.sufixo
        )

    def test_lista_e_detalhe_mostram_botao_iniciar(self):
        self.client.force_login(self.psicologo)
        url = reverse('iniciar_sessao', args=[self.sessao.pk])
        r = self.client.get(reverse('lista_sessoes'))
        self.assertContains(r, url)
        # Conta os três tipos: 1 de imagens, 1 de cartões e 1 de cenários
        self.assertEqual(r.context['sessoes'][0].total_atividades, 3)
        self.assertNotContains(r, 'name="crianca"')
        self.assertContains(
            self.client.get(reverse('detalhe_sessao', args=[self.sessao.pk])), f'{url}?crianca={self.ana.pk}'
        )


@override_settings(MEDIA_ROOT=MEDIA_TMP)
class RelatoriosTests(TestCase):
    def setUp(self):
        self.psicologo = CustomUser.objects.create_user(
            'psi', password='x', role='psicologo', aprovado=True
        )
        self.responsavel = CustomUser.objects.create_user('resp', password='x', role='responsavel')
        self.ana = Crianca.objects.create(nome='Ana Souza', data_nascimento='2018-01-01', psicologo=self.psicologo)
        self.ana.responsaveis.add(self.responsavel)
        self.bia = Crianca.objects.create(nome='Bia', data_nascimento='2018-01-01', psicologo=self.psicologo)

        self.atividade = Atividade.objects.create(
            titulo='Quem está feliz', pergunta='Quem está feliz?', emocao_correta='feliz',
            psicologo=self.psicologo,
        )
        feliz = ImagemEmocao.objects.create(atividade=self.atividade, imagem=_imagem(), emocao='feliz')
        triste = ImagemEmocao.objects.create(atividade=self.atividade, imagem=_imagem(), emocao='triste')

        # 30 dias: 1 acerto e 2 erros (escolheu Triste no lugar de Feliz)
        for imagem in (feliz, triste, triste):
            Desempenho.objects.create(
                crianca=self.ana, atividade=self.atividade, imagem_selecionada=imagem,
                correto=imagem == feliz, tempo_resposta=2.0,
            )
        # Período anterior (há 40 dias): 1 acerto
        antigo = Desempenho.objects.create(
            crianca=self.ana, atividade=self.atividade, imagem_selecionada=feliz, correto=True,
        )
        Desempenho.objects.filter(pk=antigo.pk).update(created_at=timezone.now() - timedelta(days=40))

    def test_relatorio_crianca_resume_periodo(self):
        self.client.force_login(self.psicologo)
        r = self.client.get(reverse('relatorio_crianca', args=[self.ana.pk]))
        self.assertEqual((r.context['total'], r.context['acertos']), (3, 1))
        self.assertNotContains(r, 'Em resumo')
        self.assertNotContains(r, 'Por emoção')
        self.assertNotContains(r, 'Histórico')
        self.assertContains(r, reverse('executar_atividade', args=[self.ana.pk, self.atividade.pk]))

        r = self.client.get(reverse('relatorio_crianca', args=[self.ana.pk]) + '?periodo=tudo&aba=atividade')
        self.assertEqual(r.context['total'], 4)
        self.assertEqual(r.context['aba'], 'atividade')

    def test_relatorio_geral_busca_e_ordem(self):
        self.client.force_login(self.psicologo)
        r = self.client.get(reverse('relatorio_geral'))
        # Menor taxa de acerto primeiro; quem não respondeu fica no fim
        self.assertEqual([d['crianca'] for d in r.context['dados']], [self.ana, self.bia])
        self.assertEqual(r.context['dados'][0]['taxa_pct'], 33)
        self.assertNotContains(r, 'Situação')
        self.assertNotContains(r, 'Tendência')

        r = self.client.get(reverse('relatorio_geral') + '?q=bi')
        self.assertEqual([d['crianca'] for d in r.context['dados']], [self.bia])
        r = self.client.get(reverse('relatorio_geral') + '?ordem=nome')
        self.assertEqual([d['crianca'] for d in r.context['dados']], [self.ana, self.bia])

    def test_responsavel_ve_relatorio_sem_acoes_do_psicologo(self):
        self.client.force_login(self.responsavel)
        r = self.client.get(reverse('relatorio_crianca', args=[self.ana.pk]))
        self.assertEqual(r.status_code, 200)
        self.assertNotContains(r, reverse('executar_atividade', args=[self.ana.pk, self.atividade.pk]))
        self.assertNotContains(r, reverse('relatorio_geral'))
        self.assertEqual(self.client.get(reverse('relatorio_crianca', args=[self.bia.pk])).status_code, 404)
