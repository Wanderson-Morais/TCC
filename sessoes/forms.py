from django import forms
from .models import Sessao
from atividades.models import Atividade, AtividadeCartoes, AtividadeCenario
from criancas.models import Crianca


class SessaoForm(forms.ModelForm):
    atividades = forms.ModelMultipleChoiceField(
        queryset=Atividade.objects.none(),
        widget=forms.CheckboxSelectMultiple(),
        required=False,
        label='Atividades',
    )
    atividades_cartoes = forms.ModelMultipleChoiceField(
        queryset=AtividadeCartoes.objects.none(),
        widget=forms.CheckboxSelectMultiple(),
        required=False,
        label='Atividades de Cartões Correspondentes',
    )
    atividades_cenarios = forms.ModelMultipleChoiceField(
        queryset=AtividadeCenario.objects.none(),
        widget=forms.CheckboxSelectMultiple(),
        required=False,
        label='Atividades de Organização de Emoções em Cenários',
    )
    criancas = forms.ModelMultipleChoiceField(
        queryset=Crianca.objects.none(),
        widget=forms.CheckboxSelectMultiple(),
        required=False,
        label='Crianças',
    )

    class Meta:
        model = Sessao
        fields = ['titulo', 'descricao', 'data_sessao', 'atividades', 'atividades_cartoes', 'atividades_cenarios', 'criancas']
        widgets = {
            'titulo': forms.TextInput(attrs={'class': 'form-control'}),
            'descricao': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'data_sessao': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
        }

    def __init__(self, *args, psicologo=None, **kwargs):
        super().__init__(*args, **kwargs)
        if psicologo:
            self.fields['atividades'].queryset = Atividade.objects.filter(psicologo=psicologo)
            self.fields['atividades_cartoes'].queryset = AtividadeCartoes.objects.filter(psicologo=psicologo)
            self.fields['atividades_cenarios'].queryset = AtividadeCenario.objects.filter(psicologo=psicologo)
            self.fields['criancas'].queryset = Crianca.objects.filter(psicologo=psicologo)
        if self.instance.pk:
            self.fields['atividades'].initial = self.instance.atividades.all()
            self.fields['atividades_cartoes'].initial = self.instance.atividades_cartoes.all()
            self.fields['atividades_cenarios'].initial = self.instance.atividades_cenarios.all()
            self.fields['criancas'].initial = self.instance.criancas.all()

    def save(self, commit=True):
        sessao = super().save(commit=commit)
        if commit:
            sessao.atividades.set(self.cleaned_data['atividades'])
            sessao.atividades_cartoes.set(self.cleaned_data['atividades_cartoes'])
            sessao.atividades_cenarios.set(self.cleaned_data['atividades_cenarios'])
            sessao.criancas.set(self.cleaned_data['criancas'])
        return sessao
