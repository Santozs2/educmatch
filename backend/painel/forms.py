from django import forms
from django.forms import inlineformset_factory

from avaliacao.models import LinkDeAvaliacao
from catalogo.models import Curso, Peso_curso


class NovoCurso(forms.ModelForm):
    class Meta:
        model = Curso
        fields = [
            "nome_curso",
            "descricao",
            "area_principal",
            "duracao",
            "inicio_dia",
            "fim_dia",
            "is_active",
        ]
        widgets = {
            "descricao": forms.Textarea(attrs={"rows": 3}),
            "inicio_dia": forms.DateInput(attrs={"type": "date"}),
            "fim_dia": forms.DateInput(attrs={"type": "date"}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for campo in self.fields.values():
            campo.widget.attrs["class"] = "painel-campo"


class PesoCursoForm(forms.ModelForm):
    peso = forms.IntegerField(
        min_value=0,
        max_value=5,
        widget=forms.NumberInput(attrs={"class": "painel-campo", "min": "0", "max": "5", "step": "1"}),
    )

    class Meta:
        model = Peso_curso
        fields = ("area", "peso")
        widgets = {"area": forms.Select(attrs={"class": "painel-campo"})}


PesosCursoFormSet = inlineformset_factory(
    Curso,
    Peso_curso,
    form=PesoCursoForm,
    fields=("area", "peso"),
    extra=7,
    can_delete=True,
)


class NovoLinkDeAvaliacao(forms.ModelForm):
    class Meta:
        model = LinkDeAvaliacao
        fields = ["curso", "turma"]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["curso"].queryset = Curso.objects.filter(is_active=True).order_by("nome_curso")
        self.fields["curso"].empty_label = "Escolha o curso"
        self.fields["turma"].widget.attrs["placeholder"] = "Ex.: 2026/1 · Noite"
        for campo in self.fields.values():
            campo.widget.attrs["class"] = "painel-campo"