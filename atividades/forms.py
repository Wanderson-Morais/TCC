from django import forms
from django.forms import BaseInlineFormSet, inlineformset_factory
from .models import (
    Atividade, AtividadeCartoes, AtividadeCenario, CartaoEmocao, CenarioEmocao, ImagemEmocao,
)


class AtividadeForm(forms.ModelForm):
    class Meta:
        model = Atividade
        fields = ['titulo', 'descricao', 'pergunta', 'emocao_correta']
        widgets = {
            'titulo': forms.TextInput(attrs={'class': 'form-control'}),
            'descricao': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'pergunta': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Ex: Quem está feliz?'}),
            'emocao_correta': forms.Select(attrs={'class': 'form-control'}),
        }


class ImagemEmocaoForm(forms.ModelForm):
    class Meta:
        model = ImagemEmocao
        fields = ['imagem', 'emocao', 'ordem']
        widgets = {
            'imagem': forms.ClearableFileInput(attrs={'class': 'form-control'}),
            'emocao': forms.Select(attrs={'class': 'form-control'}),
            'ordem': forms.NumberInput(attrs={'class': 'form-control', 'min': 0}),
        }


ImagemFormSet = inlineformset_factory(
    Atividade,
    ImagemEmocao,
    form=ImagemEmocaoForm,
    extra=4,
    max_num=8,
    can_delete=True,
)


class AtividadeCartoesForm(forms.ModelForm):
    class Meta:
        model = AtividadeCartoes
        fields = ['titulo', 'descricao']
        widgets = {
            'titulo': forms.TextInput(attrs={'class': 'form-control'}),
            'descricao': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
        }


class CartaoEmocaoForm(forms.ModelForm):
    class Meta:
        model = CartaoEmocao
        fields = ['palavra', 'imagem', 'emocao', 'ordem']
        widgets = {
            'palavra': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Ex: Feliz'}),
            'imagem': forms.ClearableFileInput(attrs={'class': 'form-control'}),
            'emocao': forms.Select(attrs={'class': 'form-control'}),
            'ordem': forms.NumberInput(attrs={'class': 'form-control', 'min': 0}),
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


CartaoFormSet = inlineformset_factory(
    AtividadeCartoes,
    CartaoEmocao,
    form=CartaoEmocaoForm,
    formset=BaseCartaoFormSet,
    extra=4,
    max_num=8,
    can_delete=True,
)


class AtividadeCenarioForm(forms.ModelForm):
    class Meta:
        model = AtividadeCenario
        fields = ['titulo', 'descricao']
        widgets = {
            'titulo': forms.TextInput(attrs={'class': 'form-control'}),
            'descricao': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
        }


class CenarioEmocaoForm(forms.ModelForm):
    class Meta:
        model = CenarioEmocao
        fields = ['imagem', 'descricao', 'emocao_correta', 'ordem']
        widgets = {
            'imagem': forms.ClearableFileInput(attrs={'class': 'form-control'}),
            'descricao': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Ex: A criança ganhou um bolo de aniversário.',
            }),
            'emocao_correta': forms.Select(attrs={'class': 'form-control'}),
            'ordem': forms.NumberInput(attrs={'class': 'form-control', 'min': 0}),
        }


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
    extra=4,
    max_num=8,
    can_delete=True,
)
