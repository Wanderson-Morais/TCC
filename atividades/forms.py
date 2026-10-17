from django import forms
from django.forms import BaseInlineFormSet, inlineformset_factory
from .models import (
    EMOCAO_CHOICES, Atividade, AtividadeCartoes, AtividadeCenario, CartaoEmocao, CenarioEmocao, ImagemEmocao,
)


# Rosto e pergunta sugerida para cada emoção, usados no formulário de imagens
EMOCAO_EMOJI = {
    'feliz': '😄', 'triste': '😢', 'raiva': '😠', 'medo': '😨',
    'surpresa': '😮', 'nojo': '🤢', 'neutro': '😐',
}
PERGUNTA_SUGERIDA = {
    'feliz': 'Quem está feliz?', 'triste': 'Quem está triste?', 'raiva': 'Quem está com raiva?',
    'medo': 'Quem está com medo?', 'surpresa': 'Quem está surpreso?', 'nojo': 'Quem está com nojo?',
    'neutro': 'Quem está neutro?',
}


class AtividadeForm(forms.ModelForm):
    class Meta:
        model = Atividade
        fields = ['titulo', 'descricao', 'pergunta', 'emocao_correta']
        labels = {
            'titulo': 'Nome da atividade',
            'descricao': 'Observações',
            'pergunta': 'Pergunta que a criança vai ver',
        }
        widgets = {
            'titulo': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Ex.: Encontrar o rosto feliz'}),
            'descricao': forms.Textarea(attrs={
                'class': 'form-control', 'rows': 2,
                'placeholder': 'Ex.: Usar com crianças que já reconhecem feliz e triste.',
            }),
            'pergunta': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Ex.: Quem está feliz?'}),
            'emocao_correta': forms.RadioSelect,
        }

    def opcoes_emocao(self):
        """Botões de emoção do passo 2: valor, nome, rosto, pergunta sugerida e se está marcado."""
        atual = self['emocao_correta'].value()
        return [
            {
                'valor': valor, 'nome': nome, 'emoji': EMOCAO_EMOJI.get(valor, ''),
                'pergunta': PERGUNTA_SUGERIDA.get(valor, ''), 'marcada': valor == atual,
            }
            for valor, nome in EMOCAO_CHOICES
        ]


class ImagemEmocaoForm(forms.ModelForm):
    class Meta:
        model = ImagemEmocao
        fields = ['imagem', 'emocao', 'ordem']
        labels = {'emocao': 'Emoção desta imagem'}
        widgets = {
            'imagem': forms.FileInput(attrs={'class': 'arquivo-oculto', 'accept': 'image/*', 'data-arquivo': ''}),
            'emocao': forms.Select(attrs={'class': 'form-control', 'data-emocao': ''}),
            # A ordem é a posição do cartão na tela; o JavaScript preenche ao salvar
            'ordem': forms.HiddenInput(attrs={'data-ordem': ''}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['emocao'].choices = [('', 'Escolha…')] + [
            (valor, f'{EMOCAO_EMOJI.get(valor, "")} {nome}') for valor, nome in EMOCAO_CHOICES
        ]

    def has_changed(self):
        # A ordem é preenchida em todos os cartões; uma caixa vazia só com ordem continua vazia
        return any(campo != 'ordem' for campo in self.changed_data)


class BaseImagemFormSet(BaseInlineFormSet):
    # Definida pela view antes de validar: a emoção que é a resposta certa
    emocao_correta = None

    def clean(self):
        super().clean()
        if any(self.errors):
            return
        imagens = [
            f.cleaned_data for f in self.forms
            if f.cleaned_data and not f.cleaned_data.get('DELETE') and f.cleaned_data.get('imagem')
        ]
        if len(imagens) < 2:
            raise forms.ValidationError('Adicione pelo menos 2 imagens.')
        if self.emocao_correta and not any(i.get('emocao') == self.emocao_correta for i in imagens):
            raise forms.ValidationError('Pelo menos uma imagem precisa mostrar a emoção certa.')


ImagemFormSet = inlineformset_factory(
    Atividade,
    ImagemEmocao,
    form=ImagemEmocaoForm,
    formset=BaseImagemFormSet,
    extra=4,
    max_num=8,
    can_delete=True,
)
# Na edição só aparecem as imagens que já existem; novas entram pelo "Adicionar imagem"
ImagemFormSetEdicao = inlineformset_factory(
    Atividade,
    ImagemEmocao,
    form=ImagemEmocaoForm,
    formset=BaseImagemFormSet,
    extra=0,
    max_num=8,
    can_delete=True,
)


class AtividadeCartoesForm(forms.ModelForm):
    class Meta:
        model = AtividadeCartoes
        fields = ['titulo', 'descricao']
        labels = {'titulo': 'Nome da atividade', 'descricao': 'Observações'}
        widgets = {
            'titulo': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Ex.: Pares das emoções básicas'}),
            'descricao': forms.Textarea(attrs={
                'class': 'form-control', 'rows': 2, 'placeholder': 'Ex.: Começar com feliz e triste.',
            }),
        }


class CartaoEmocaoForm(forms.ModelForm):
    # Sem "ordem": a tela da criança embaralha palavras e rostos
    class Meta:
        model = CartaoEmocao
        fields = ['palavra', 'imagem', 'emocao']
        labels = {'palavra': 'Palavra no cartão'}
        widgets = {
            'palavra': forms.TextInput(attrs={'class': 'form-control', 'data-palavra': ''}),
            'imagem': forms.FileInput(attrs={'class': 'arquivo-oculto', 'accept': 'image/*', 'data-arquivo': ''}),
            'emocao': forms.HiddenInput,
        }


class BaseCartaoFormSet(BaseInlineFormSet):
    def clean(self):
        super().clean()
        if any(self.errors):
            return
        emocoes = [
            f.cleaned_data['emocao']
            for f in self.forms
            if f.cleaned_data and not f.cleaned_data.get('DELETE') and f.cleaned_data.get('emocao')
        ]
        if len(emocoes) < 2:
            raise forms.ValidationError('Adicione pelo menos 2 cartões.')
        if len(emocoes) != len(set(emocoes)):
            raise forms.ValidationError('Cada emoção só pode aparecer em um cartão.')

    def pares(self):
        """Um item por emoção, na ordem das emoções: o formulário e se o par está escolhido."""
        nomes = dict(EMOCAO_CHOICES)
        ordem = [valor for valor, _ in EMOCAO_CHOICES]
        itens = []
        for f in self.forms:
            valor = f['emocao'].value()
            if f.is_bound:
                escolhido = not f['DELETE'].value()
            else:
                escolhido = bool(f.instance.pk)
            itens.append({
                'valor': valor, 'nome': nomes.get(valor, valor), 'emoji': EMOCAO_EMOJI.get(valor, ''),
                'form': f, 'escolhido': escolhido,
            })
        itens.sort(key=lambda p: ordem.index(p['valor']) if p['valor'] in ordem else len(ordem))
        return itens


def cartao_formset(data=None, files=None, instance=None):
    """Formset com um par por emoção: os cartões que já existem e um vazio para cada emoção que falta."""
    usadas = set(instance.cartoes.values_list('emocao', flat=True)) if instance and instance.pk else set()
    faltando = [(valor, nome) for valor, nome in EMOCAO_CHOICES if valor not in usadas]
    FormSet = inlineformset_factory(
        AtividadeCartoes,
        CartaoEmocao,
        form=CartaoEmocaoForm,
        formset=BaseCartaoFormSet,
        extra=len(faltando),
        max_num=len(EMOCAO_CHOICES),
        can_delete=True,
    )
    return FormSet(
        data, files, instance=instance,
        initial=[{'emocao': valor, 'palavra': nome} for valor, nome in faltando],
    )


class AtividadeCenarioForm(forms.ModelForm):
    class Meta:
        model = AtividadeCenario
        fields = ['titulo', 'descricao']
        labels = {'titulo': 'Nome da atividade', 'descricao': 'Observações'}
        widgets = {
            'titulo': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Ex.: Emoções no dia a dia'}),
            'descricao': forms.Textarea(attrs={
                'class': 'form-control', 'rows': 2, 'placeholder': 'Ex.: Situações em casa e na escola.',
            }),
        }


class CenarioEmocaoForm(forms.ModelForm):
    class Meta:
        model = CenarioEmocao
        fields = ['imagem', 'descricao', 'emocao_correta', 'ordem']
        labels = {'descricao': 'O que está acontecendo?', 'emocao_correta': 'Emoção certa'}
        widgets = {
            'imagem': forms.FileInput(attrs={'class': 'arquivo-oculto', 'accept': 'image/*', 'data-arquivo': ''}),
            'descricao': forms.Textarea(attrs={
                'class': 'form-control', 'rows': 3, 'data-descricao': '',
                'placeholder': 'Ex.: Hoje é o aniversário do Theo. Ele ganhou um bolo com velinhas. '
                               'Como o Theo está se sentindo?',
            }),
            'emocao_correta': forms.RadioSelect,
            # A ordem é a posição da cena na lista; o JavaScript preenche ao salvar
            'ordem': forms.HiddenInput(attrs={'data-ordem': ''}),
        }

    def opcoes_emocao(self):
        """Botões de emoção da cena: valor, nome, rosto e se está marcado."""
        atual = self['emocao_correta'].value()
        return [
            {'valor': valor, 'nome': nome, 'emoji': EMOCAO_EMOJI.get(valor, ''), 'marcada': valor == atual}
            for valor, nome in EMOCAO_CHOICES
        ]

    def has_changed(self):
        # A ordem é preenchida em todas as cenas; uma cena vazia só com ordem continua vazia
        return any(campo != 'ordem' for campo in self.changed_data)


class BaseCenarioFormSet(BaseInlineFormSet):
    def clean(self):
        super().clean()
        if any(self.errors):
            return
        emocoes = [
            f.cleaned_data['emocao_correta']
            for f in self.forms
            if f.cleaned_data and not f.cleaned_data.get('DELETE') and f.cleaned_data.get('emocao_correta')
        ]
        if len(emocoes) < 2:
            raise forms.ValidationError('Adicione pelo menos 2 cenários.')
        if len(set(emocoes)) < 2:
            raise forms.ValidationError('Os cenários precisam ter pelo menos 2 emoções diferentes.')


CenarioFormSet = inlineformset_factory(
    AtividadeCenario,
    CenarioEmocao,
    form=CenarioEmocaoForm,
    formset=BaseCenarioFormSet,
    extra=2,
    max_num=8,
    can_delete=True,
)
# Na edição só aparecem as cenas que já existem; novas entram pelo "Adicionar cena"
CenarioFormSetEdicao = inlineformset_factory(
    AtividadeCenario,
    CenarioEmocao,
    form=CenarioEmocaoForm,
    formset=BaseCenarioFormSet,
    extra=0,
    max_num=8,
    can_delete=True,
)
