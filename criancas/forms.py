from django import forms
from .models import Crianca
from accounts.models import CustomUser


class CriancaForm(forms.ModelForm):
    class Meta:
        model = Crianca
        fields = ['nome', 'data_nascimento', 'foto', 'observacoes', 'responsaveis']
        widgets = {
            'nome': forms.TextInput(attrs={'class': 'form-control'}),
            'data_nascimento': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'foto': forms.ClearableFileInput(attrs={'class': 'form-control'}),
            'observacoes': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'responsaveis': forms.CheckboxSelectMultiple(),
        }

    def __init__(self, *args, psicologo=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['responsaveis'].queryset = CustomUser.objects.filter(
            role=CustomUser.ROLE_RESPONSAVEL
        )
        self.fields['responsaveis'].required = False
