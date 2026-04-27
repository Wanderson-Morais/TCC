from django import forms
from .models import Sessao
from atividades.models import Atividade
from criancas.models import Crianca


class SessaoForm(forms.ModelForm):
    atividades = forms.ModelMultipleChoiceField(
        queryset=Atividade.objects.none(),
        widget=forms.CheckboxSelectMultiple(),
        required=False,
        label='Atividades',
    )
    criancas = forms.ModelMultipleChoiceField(
        queryset=Crianca.objects.none(),
        widget=forms.CheckboxSelectMultiple(),
        required=False,
        label='Crianças',
    )

    class Meta:
        model = Sessao
        fields = ['titulo', 'descricao', 'data_sessao', 'atividades', 'criancas']
        widgets = {
            'titulo': forms.TextInput(attrs={'class': 'form-control'}),
            'descricao': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'data_sessao': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
        }

    def __init__(self, *args, psicologo=None, **kwargs):
        super().__init__(*args, **kwargs)
        if psicologo:
            self.fields['atividades'].queryset = Atividade.objects.filter(psicologo=psicologo)
            self.fields['criancas'].queryset = Crianca.objects.filter(psicologo=psicologo)
        if self.instance.pk:
            self.fields['atividades'].initial = self.instance.atividades.all()
            self.fields['criancas'].initial = self.instance.criancas.all()

    def save(self, commit=True):
        sessao = super().save(commit=commit)
        if commit:
            sessao.atividades.set(self.cleaned_data['atividades'])
            sessao.criancas.set(self.cleaned_data['criancas'])
        return sessao
