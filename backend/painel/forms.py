from django import forms
from django.db.models import Q
from django.forms import BaseInlineFormSet, inlineformset_factory
from django.utils.text import slugify

from avaliacao.models import LinkDeAvaliacao
from catalogo.models import Area, Curso, Peso_curso


def areas_escolhiveis(area_atual_id=None):
    """Só áreas ativas. A que o registro já usa fica, para editar não trocar a área dele."""
    return Area.objects.filter(Q(is_active=True) | Q(pk=area_atual_id))


def opcoes_de_area(campo, areas, area_atual_id):
    """A regra de areas_escolhiveis aplicada a Area.objects.all() já carregado, sem nova consulta."""
    opcoes = [] if campo.empty_label is None else [("", campo.empty_label)]
    opcoes += [
        (area.pk, campo.label_from_instance(area))
        for area in areas
        if area.is_active or area.pk == area_atual_id
    ]
    return opcoes


class NovoCurso(forms.ModelForm):
    class Meta:
        model = Curso
        fields = [
            "nome_curso",
            "descricao",
            "area_principal",
            "nivel",
            "modalidade",
            "duracao",
            "unidade_carga",
            "url_senai",
            "inicio_dia",
            "fim_dia",
            "is_active",
        ]
        labels = {
            "nivel": "Nível",
            "unidade_carga": "Unidade da carga",
            "url_senai": "Link no site do SENAI",
        }
        widgets = {
            "descricao": forms.Textarea(attrs={"rows": 3}),
            "inicio_dia": forms.DateInput(attrs={"type": "date"}),
            "fim_dia": forms.DateInput(attrs={"type": "date"}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Guardada aqui: validar um POST troca a área da instância pela enviada.
        self.area_atual_id = self.instance.area_principal_id
        self.fields["area_principal"].queryset = areas_escolhiveis(self.area_atual_id)
        for campo in self.fields.values():
            campo.widget.attrs["class"] = "painel-campo"

    def usar_areas(self, areas):
        """Só muda o que o select desenha: a validação continua no queryset."""
        campo = self.fields["area_principal"]
        campo.choices = opcoes_de_area(campo, areas, self.area_atual_id)


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

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.area_atual_id = self.instance.area_id
        self.fields["area"].queryset = areas_escolhiveis(self.area_atual_id)

    def usar_areas(self, areas):
        campo = self.fields["area"]
        campo.choices = opcoes_de_area(campo, areas, self.area_atual_id)

    def has_changed(self):
        """Linha sem área é linha em branco.

        O peso declarado aqui não herda o default do model, então o "0" que o
        navegador envia nas linhas extras contaria como alteração e gravaria um
        Peso_curso sem área.
        """
        if not self.data.get(self.add_prefix("area")):
            return False
        return super().has_changed()


class BasePesosCursoFormSet(BaseInlineFormSet):
    def get_queryset(self):
        """Com prefetch_related("curso_peso") no curso, as linhas não voltam ao banco."""
        prefetch = getattr(self.instance, "_prefetched_objects_cache", {})
        if not hasattr(self, "_queryset") and "curso_peso" in prefetch:
            self._queryset = prefetch["curso_peso"]
        return super().get_queryset()

    def usar_areas(self, areas):
        for form in self.forms:
            form.usar_areas(areas)


PesosCursoFormSet = inlineformset_factory(
    Curso,
    Peso_curso,
    form=PesoCursoForm,
    formset=BasePesosCursoFormSet,
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

