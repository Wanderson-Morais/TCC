from django import forms
from django.forms import inlineformset_factory
from .models import Atividade, ImagemEmocao


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
