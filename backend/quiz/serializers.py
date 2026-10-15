"""Revista da saída da LLM: nada entra no banco sem passar por aqui."""
import json
from dataclasses import dataclass

from rest_framework import serializers

from quiz.llm import LLMInvalidOutput

LIMITE_PRINCIPAL = 600   # regra 7 do prompt
LIMITE_ALTERNATIVA = 220


class PrincipalSerializer(serializers.Serializer):
    course_id = serializers.IntegerField()
    texto = serializers.CharField(max_length=LIMITE_PRINCIPAL)  # já recusa vazio


class AlternativaSerializer(serializers.Serializer):
    course_id = serializers.IntegerField()
    texto = serializers.CharField(max_length=LIMITE_ALTERNATIVA)


class DeliverySerializer(serializers.Serializer):
    """As regras do contrato de saída. Precisa de `candidatos` e `tie_set` no context."""

    principal = PrincipalSerializer()
    alternativas = AlternativaSerializer(many=True)

    def validate(self, dados):
        ids = [dados["principal"]["course_id"]] + [a["course_id"] for a in dados["alternativas"]]
        candidatos = self.context["candidatos"]

        if len(ids) != len(set(ids)):
            raise serializers.ValidationError("curso repetido")
        if set(ids) - set(candidatos):
            raise serializers.ValidationError("curso fora da lista de candidatos")
        if set(candidatos) - set(ids):
            raise serializers.ValidationError("faltou curso: a LLM não pode descartar candidato")
        if ids[0] not in self.context["tie_set"]:
            raise serializers.ValidationError("regra 2: o principal não está no tie_set")
        return dados


@dataclass(frozen=True)
class Entrega:
    """A saída aprovada: a ordem final (o principal primeiro) e o texto de cada curso.

    Os campos com padrão são os dados da chamada, preenchidos pelo deliver (Passo 9).
    """

    ordem: list[int]
    textos: dict[int, str]
    modelo: str = ""
    tokens_in: int | None = None
    tokens_out: int | None = None
    cache_hit: bool = False


def ler_json(texto):
    """Tolera cerca de código e texto em volta: pega do primeiro { ao último }."""
    inicio, fim = texto.find("{"), texto.rfind("}")
    if inicio == -1 or fim < inicio:
        raise LLMInvalidOutput("a resposta não tem JSON")
    try:
        return json.loads(texto[inicio:fim + 1])
    except ValueError as erro:
        raise LLMInvalidOutput(f"JSON quebrado: {erro}") from None


def validate_delivery(texto, payload):
    """Entrega aprovada, ou LLMInvalidOutput com o motivo."""
    serializer = DeliverySerializer(
        data=ler_json(texto),
        context={
            "candidatos": [c["course_id"] for c in payload["candidatos"]],
            "tie_set": payload["tie_set"],
        },
    )
    if not serializer.is_valid():
        raise LLMInvalidOutput(f"saída recusada: {serializer.errors}")

    dados = serializer.validated_data
    itens = [dados["principal"], *dados["alternativas"]]
    return Entrega(
        ordem=[item["course_id"] for item in itens],
        textos={item["course_id"]: item["texto"] for item in itens},
    )