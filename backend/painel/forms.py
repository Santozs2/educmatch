from django import forms
from django.forms import inlineformset_factory
from django.utils.text import slugify

from avaliacao.models import LinkDeAvaliacao
from catalogo.models import Area, Curso, Peso_curso


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


class NovaArea(forms.ModelForm):
    """Cria uma Area do catálogo. O slug sai do nome: quem cadastra não digita chave."""

    class Meta:
        model = Area
        fields = ["nome", "descricao"]
        widgets = {"descricao": forms.Textarea(attrs={"rows": 3})}

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["nome"].widget.attrs["placeholder"] = "Ex.: Elétrica"
        for campo in self.fields.values():
            campo.widget.attrs["class"] = "painel-campo"

    # Validação do nome: não pode haver duas áreas com o mesmo nome (case insensitive).
    def clean_nome(self):
        nome = self.cleaned_data["nome"].strip()
        existentes = Area.objects.filter(nome__iexact=nome)
        if self.instance.pk:
            existentes = existentes.exclude(pk=self.instance.pk)
        if existentes.exists():
            raise forms.ValidationError("Já existe uma área com esse nome.")
        return nome

    def save(self, commit=True):
        area = super().save(commit=False)
        if not area.slug:
            area.slug = self._slug_livre(slugify(area.nome))
        if commit:
            area.save()
        return area

    @staticmethod
    def _slug_livre(base):
        """O slug é a chave estável do matching, então não pode colidir nem ficar vazio."""
        base = base or "area"
        slug = base
        sufixo = 2
        while Area.objects.filter(slug=slug).exists():
            slug = f"{base}-{sufixo}"
            sufixo += 1
        return slug


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

    def has_changed(self):
        """Linha sem área é linha em branco.

        O peso declarado aqui não herda o default do model, então o "0" que o
        navegador envia nas linhas extras contaria como alteração e gravaria um
        Peso_curso sem área.
        """
        if not self.data.get(self.add_prefix("area")):
            return False
        return super().has_changed()


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

