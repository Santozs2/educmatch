from django import forms


def _campo(pergunta):
    """Um campo do Django para cada tipo de pergunta."""
    comum = {"label": pergunta.texto, "required": pergunta.obrigatoria}
    if pergunta.tipo == "nps":
        return forms.TypedChoiceField(
            choices=[(n, n) for n in range(11)], coerce=int, widget=forms.RadioSelect, **comum
        )
    if pergunta.tipo == "escala":
        return forms.TypedChoiceField(
            choices=[(n, n) for n in range(1, 6)], coerce=int, widget=forms.RadioSelect, **comum
        )
    if pergunta.tipo == "escolha":
        return forms.ChoiceField(
            choices=[(opcao, opcao) for opcao in pergunta.opcoes], widget=forms.RadioSelect, **comum
        )
    return forms.CharField(max_length=1000, widget=forms.Textarea(attrs={"rows": 4}), **comum)


class FormularioDeAvaliacao(forms.Form):
    """Montado na hora a partir das perguntas ativas: trocar o seed troca o formulário."""

    def __init__(self, perguntas, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.perguntas = list(perguntas)
        for pergunta in self.perguntas:
            self.fields[f"pergunta_{pergunta.id}"] = _campo(pergunta)

    def campos_por_pergunta(self):
        """(pergunta, campo do form) na ordem, para o template saber o tipo de cada um."""
        return [(pergunta, self[f"pergunta_{pergunta.id}"]) for pergunta in self.perguntas]