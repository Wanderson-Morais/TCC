import shutil
import tempfile
from io import BytesIO

from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase, override_settings
from django.urls import reverse
from PIL import Image

from accounts.models import CustomUser
from .models import (
    EMOCAO_CHOICES, Atividade, AtividadeCartoes, AtividadeCenario, CartaoEmocao, CenarioEmocao, ImagemEmocao,
)

MEDIA_TMP = tempfile.mkdtemp()


def _imagem(nome='rosto.png'):
    buf = BytesIO()
    Image.new('RGB', (10, 10)).save(buf, 'PNG')
    return SimpleUploadedFile(nome, buf.getvalue(), content_type='image/png')


@override_settings(MEDIA_ROOT=MEDIA_TMP)
class FormularioAtividadeImagensTests(TestCase):
    @classmethod
    def tearDownClass(cls):
        super().tearDownClass()
        shutil.rmtree(MEDIA_TMP, ignore_errors=True)

    def setUp(self):
        self.psicologo = CustomUser.objects.create_user(
            'psi', password='x', role='psicologo', aprovado=True
        )
        self.client.force_login(self.psicologo)

    def _dados(self, imagens, emocao_correta='feliz', total=4, iniciais=0):
        dados = {
            'titulo': 'Rosto feliz', 'descricao': '', 'pergunta': 'Quem está feliz?',
            'emocao_correta': emocao_correta,
            'imagens-TOTAL_FORMS': str(total), 'imagens-INITIAL_FORMS': str(iniciais),
            'imagens-MIN_NUM_FORMS': '0', 'imagens-MAX_NUM_FORMS': '8',
        }
        # Como o JavaScript: todas as caixas recebem ordem, inclusive as vazias
        for i in range(total):
            dados[f'imagens-{i}-ordem'] = str(i)
        for i, emocao in enumerate(imagens):
            dados[f'imagens-{i}-emocao'] = emocao
            dados[f'imagens-{i}-imagem'] = _imagem(f'{i}.png')
        return dados

    def test_pagina_mostra_os_tres_passos(self):
        r = self.client.get(reverse('criar_atividade'))
        self.assertContains(r, 'Dê um nome à atividade')
        self.assertContains(r, 'Qual emoção a criança vai procurar?')
        self.assertContains(r, 'Adicione as imagens')
        self.assertContains(r, 'data-pergunta="Quem está com medo?"')
        self.assertContains(r, 'id="modelo-imagem"')
        self.assertEqual(len(r.context['formset'].forms), 4)

    def test_cria_atividade_na_ordem_dos_cartoes(self):
        r = self.client.post(reverse('criar_atividade'), self._dados(['medo', 'feliz', 'triste']))
        atividade = Atividade.objects.get(titulo='Rosto feliz')
        self.assertRedirects(r, reverse('detalhe_atividade', args=[atividade.pk]))
        self.assertEqual(
            list(atividade.imagens.order_by('ordem').values_list('emocao', flat=True)),
            ['medo', 'feliz', 'triste'],
        )

    def test_exige_duas_imagens(self):
        r = self.client.post(reverse('criar_atividade'), self._dados(['feliz']))
        self.assertContains(r, 'Adicione pelo menos 2 imagens.')
        self.assertFalse(Atividade.objects.exists())

    def test_exige_imagem_com_a_emocao_certa(self):
        r = self.client.post(reverse('criar_atividade'), self._dados(['medo', 'triste']))
        self.assertContains(r, 'Pelo menos uma imagem precisa mostrar a emoção certa.')
        self.assertFalse(Atividade.objects.exists())

    def test_edicao_mostra_so_as_imagens_existentes(self):
        atividade = Atividade.objects.create(
            titulo='A', pergunta='Quem está feliz?', emocao_correta='feliz', psicologo=self.psicologo,
        )
        for i, emocao in enumerate(['feliz', 'triste']):
            ImagemEmocao.objects.create(atividade=atividade, imagem=_imagem(), emocao=emocao, ordem=i)
        r = self.client.get(reverse('editar_atividade', args=[atividade.pk]))
        self.assertEqual(len(r.context['formset'].forms), 2)
        self.assertContains(r, 'Editar Atividade de Imagens')


@override_settings(MEDIA_ROOT=MEDIA_TMP)
class FormularioCartoesTests(TestCase):
    def setUp(self):
        self.psicologo = CustomUser.objects.create_user(
            'psi', password='x', role='psicologo', aprovado=True
        )
        self.client.force_login(self.psicologo)

    def _post(self, formset, escolhidas, fotos, titulo='Pares'):
        """Simula o navegador: um par por emoção; os não escolhidos vão com DELETE marcado."""
        dados = {
            'titulo': titulo, 'descricao': '',
            'cartoes-TOTAL_FORMS': str(len(formset.forms)),
            'cartoes-INITIAL_FORMS': str(formset.initial_form_count()),
            'cartoes-MIN_NUM_FORMS': '0', 'cartoes-MAX_NUM_FORMS': '7',
        }
        for i, f in enumerate(formset.forms):
            emocao = f['emocao'].value()
            dados[f'cartoes-{i}-emocao'] = emocao
            dados[f'cartoes-{i}-palavra'] = f['palavra'].value()
            if f.instance.pk:
                dados[f'cartoes-{i}-id'] = str(f.instance.pk)
            if emocao not in escolhidas:
                dados[f'cartoes-{i}-DELETE'] = 'on'
            if emocao in fotos:
                dados[f'cartoes-{i}-imagem'] = _imagem(f'{emocao}.png')
        return dados

    def test_pagina_tem_um_par_por_emocao(self):
        r = self.client.get(reverse('criar_atividade_cartoes'))
        self.assertContains(r, 'Quais emoções vão ter um par?')
        pares = r.context['formset'].pares()
        self.assertEqual([p['valor'] for p in pares], [v for v, _ in EMOCAO_CHOICES])
        self.assertFalse(any(p['escolhido'] for p in pares))

    def test_cria_so_os_pares_escolhidos(self):
        formset = self.client.get(reverse('criar_atividade_cartoes')).context['formset']
        r = self.client.post(reverse('criar_atividade_cartoes'), self._post(formset, {'feliz', 'triste'}, {'feliz', 'triste'}))
        atividade = AtividadeCartoes.objects.get(titulo='Pares')
        self.assertRedirects(r, reverse('detalhe_atividade_cartoes', args=[atividade.pk]))
        self.assertEqual(
            sorted(atividade.cartoes.values_list('emocao', 'palavra')),
            [('feliz', 'Feliz'), ('triste', 'Triste')],
        )

    def test_edicao_desmarca_e_marca_emocoes(self):
        atividade = AtividadeCartoes.objects.create(titulo='Pares', psicologo=self.psicologo)
        for emocao, palavra in [('feliz', 'Feliz'), ('triste', 'Triste')]:
            CartaoEmocao.objects.create(atividade=atividade, palavra=palavra, imagem=_imagem(), emocao=emocao)
        url = reverse('editar_atividade_cartoes', args=[atividade.pk])
        formset = self.client.get(url).context['formset']
        self.assertEqual(len(formset.forms), 7)
        self.assertEqual({p['valor'] for p in formset.pares() if p['escolhido']}, {'feliz', 'triste'})

        r = self.client.post(url, self._post(formset, {'feliz', 'medo'}, {'medo'}))
        self.assertRedirects(r, reverse('detalhe_atividade_cartoes', args=[atividade.pk]))
        self.assertEqual(sorted(atividade.cartoes.values_list('emocao', flat=True)), ['feliz', 'medo'])


@override_settings(MEDIA_ROOT=MEDIA_TMP)
class FormularioCenariosTests(TestCase):
    def setUp(self):
        self.psicologo = CustomUser.objects.create_user(
            'psi', password='x', role='psicologo', aprovado=True
        )
        self.client.force_login(self.psicologo)

    def _dados(self, cenas, total=3):
        dados = {
            'titulo': 'Dia a dia', 'descricao': '',
            'cenarios-TOTAL_FORMS': str(total), 'cenarios-INITIAL_FORMS': '0',
            'cenarios-MIN_NUM_FORMS': '0', 'cenarios-MAX_NUM_FORMS': '8',
        }
        # Como o JavaScript: todas as cenas recebem ordem, inclusive as vazias
        for i in range(total):
            dados[f'cenarios-{i}-ordem'] = str(i)
        for i, (descricao, emocao) in enumerate(cenas):
            dados[f'cenarios-{i}-descricao'] = descricao
            dados[f'cenarios-{i}-emocao_correta'] = emocao
            dados[f'cenarios-{i}-imagem'] = _imagem(f'{i}.png')
        return dados

    def test_pagina_mostra_os_dois_passos(self):
        r = self.client.get(reverse('criar_atividade_cenario'))
        self.assertContains(r, 'Monte as cenas')
        self.assertContains(r, 'cada cena conta como uma atividade')
        self.assertContains(r, 'id="modelo-cena"')
        self.assertEqual(len(r.context['formset'].forms), 2)

    def test_cria_cenas_na_ordem_da_lista(self):
        dados = self._dados([('Ganhou um bolo', 'feliz'), ('O robô quebrou', 'triste')])
        r = self.client.post(reverse('criar_atividade_cenario'), dados)
        atividade = AtividadeCenario.objects.get(titulo='Dia a dia')
        self.assertRedirects(r, reverse('detalhe_atividade_cenario', args=[atividade.pk]))
        self.assertEqual(
            list(atividade.cenarios.values_list('descricao', 'emocao_correta')),
            [('Ganhou um bolo', 'feliz'), ('O robô quebrou', 'triste')],
        )

    def test_exige_duas_emocoes_diferentes(self):
        r = self.client.post(reverse('criar_atividade_cenario'), self._dados([('A', 'feliz'), ('B', 'feliz')]))
        self.assertContains(r, 'pelo menos 2 emoções diferentes')
        self.assertFalse(AtividadeCenario.objects.exists())

    def test_edicao_mostra_so_as_cenas_existentes(self):
        atividade = AtividadeCenario.objects.create(titulo='Dia a dia', psicologo=self.psicologo)
        for i, emocao in enumerate(['feliz', 'triste']):
            CenarioEmocao.objects.create(
                atividade=atividade, imagem=_imagem(), descricao=f'Cena {i}', emocao_correta=emocao, ordem=i,
            )
        r = self.client.get(reverse('editar_atividade_cenario', args=[atividade.pk]))
        self.assertEqual(len(r.context['formset'].forms), 2)
        self.assertContains(r, 'value="triste"')
