"""Consultor de cursos: a LLM sugere áreas, nome e descrição no cadastro de um curso.

Só lê. Nada aqui grava no banco: quem aceita a sugestão e salva o curso é o
administrador, pelo formulário de sempre. O que precisa ser confiável (cursos
parecidos, possível duplicidade, áreas que existem) é calculado em Python; a
LLM só escreve a análise, e a saída dela passa pela revisão de saida_valida.
"""
import hashlib
import json
import logging
import math
import re
import unicodedata
from dataclasses import dataclass, field
from difflib import SequenceMatcher
from functools import lru_cache
from pathlib import Path

from django.conf import settings
from django.core.cache import cache
from django.db.models import Count, Q
from rest_framework import serializers

from catalogo.models import Area, Curso
from quiz.llm import LLMInvalidOutput, LLMUnavailable, get_provider
from quiz.models import Peso_alternativa
from quiz.serializers import ler_json

logger = logging.getLogger(__name__)

PROMPT_VERSION = "v1"
PASTA = Path(__file__).resolve().parent / "prompts"

MINIMO_DESCRICAO = 30      # menos que isso não dá para classificar
MAXIMO_TEXTO = 3000        # o que vai para o prompt; o resto é cortado
SEMELHANTES = 6
CORTE_SEMELHANCA = 0.12
CORTE_DUPLICADO = 0.85     # nomes quase iguais
CACHE_SEGUNDOS = 24 * 60 * 60

PALAVRAS_VAZIAS = set(
    "para com sem por pela pelo das dos nas nos uma uns umas que como entre sobre "
    "seu sua seus suas este esta isso esse essa curso cursos aluno alunos basico "
    "basica nivel area areas the and".split()
)


class EntradaInvalida(ValueError):
    """O que o admin mandou não dá para analisar. A mensagem vai para a tela."""


# ---------- Contexto (Python) ----------

def normalizar(texto):
    sem_acento = unicodedata.normalize("NFD", texto or "").encode("ascii", "ignore").decode()
    return re.sub(r"\s+", " ", re.sub(r"[^a-z0-9 ]", " ", sem_acento.lower())).strip()


def palavras(texto):
    return {p for p in normalizar(texto).split() if len(p) > 2 and p not in PALAVRAS_VAZIAS}


def _semelhanca(a, b):
    """Palavras em comum, pelo tamanho dos dois textos (cosseno de conjuntos)."""
    if not a or not b:
        return 0.0
    return len(a & b) / math.sqrt(len(a) * len(b))


def cursos_semelhantes(nome, descricao, ignorar_id=None):
    """Os cursos ativos mais parecidos com o informado, com a nota de semelhança.

    O nome pesa em dobro: dois cursos com o mesmo nome e descrições diferentes
    ainda são candidatos a duplicidade.
    """
    alvo_nome, alvo_tudo = palavras(nome), palavras(f"{nome} {descricao}")
    nome_normal = normalizar(nome)
    cursos = (
        Curso.objects.filter(is_active=True)
        .exclude(pk=ignorar_id)
        .select_related("area_principal")
        .prefetch_related("curso_peso__area")
    )
    achados = []
    for curso in cursos:
        nota = (
            2 * _semelhanca(alvo_nome, palavras(curso.nome_curso))
            + _semelhanca(alvo_tudo, palavras(f"{curso.nome_curso} {curso.descricao}"))
        ) / 3
        mesmo_nome = bool(nome_normal) and (
            SequenceMatcher(None, nome_normal, normalizar(curso.nome_curso)).ratio() >= CORTE_DUPLICADO
        )
        if nota >= CORTE_SEMELHANCA or mesmo_nome:
            achados.append((curso, round(nota, 3), mesmo_nome))
    # Desempate pelo id: o prompt é a chave do cache e precisa sair igual a cada pedido.
    achados.sort(key=lambda item: (item[2], item[1], -item[0].pk), reverse=True)
    return achados[:SEMELHANTES]


def areas_do_catalogo():
    """As áreas ativas, com o que a LLM precisa para julgar uma área nova com justiça."""
    no_quiz = set(
        Peso_alternativa.objects.filter(peso__gt=0, alternativa__questao__is_active=True)
        .values_list("area_id", flat=True)
    )
    # Com GROUP BY o Django ignora o Meta.ordering: a ordem vai explícita.
    areas = Area.objects.filter(is_active=True).annotate(
        ativos=Count("cursos", filter=Q(cursos__is_active=True))
    ).order_by("nome")
    return [
        {
            "id": area.pk,
            "slug": area.slug,
            "nome": area.nome,
            "descricao": area.descricao,
            "cursos_ativos": area.ativos,
            "tem_pesos_no_quiz": area.pk in no_quiz,
        }
        for area in areas
    ]


def montar_contexto(nome, descricao, ignorar_id=None):
    nome = (nome or "").strip()[:150]
    descricao = (descricao or "").strip()[:MAXIMO_TEXTO]
    if len(descricao) < MINIMO_DESCRICAO:
        raise EntradaInvalida(
            f"Escreva uma descrição com pelo menos {MINIMO_DESCRICAO} caracteres para o consultor analisar."
        )
    areas = areas_do_catalogo()
    if not areas:
        raise EntradaInvalida("Não há áreas ativas cadastradas para recomendar.")
    semelhantes = cursos_semelhantes(nome, descricao, ignorar_id)
    return {
        "curso": {"nome": nome, "descricao": descricao},
        "areas": areas,
        "semelhantes": [
            {
                "id": curso.pk,
                "nome": curso.nome_curso,
                "descricao": curso.descricao[:400],
                "area_principal": curso.area_principal.slug,
                # Ordenado pelo slug: com pesos empatados, o banco devolve as linhas em qualquer ordem.
                "pesos": dict(sorted((p.area.slug, int(p.peso)) for p in curso.curso_peso.all() if p.area)),
                "semelhanca": nota,
                "possivel_duplicado": duplicado,
            }
            for curso, nota, duplicado in semelhantes
        ],
    }


# ---------- Prompt ----------

@lru_cache
def carregar_prompt(versao=PROMPT_VERSION):
    return (PASTA / f"consultor_{versao}.md").read_text(encoding="utf-8")


def _json(valor):
    return json.dumps(valor, ensure_ascii=False, indent=2)


def montar_prompt(contexto):
    """Só o que a LLM precisa: o id interno das áreas fica de fora."""
    areas = [{k: v for k, v in area.items() if k != "id"} for area in contexto["areas"]]
    semelhantes = [{k: v for k, v in c.items() if k != "id"} for c in contexto["semelhantes"]]
    return (
        carregar_prompt()
        .replace("{{CURSO_JSON}}", _json(contexto["curso"]))
        .replace("{{AREAS_JSON}}", _json(areas))
        .replace("{{SEMELHANTES_JSON}}", _json(semelhantes))
    )


# ---------- Revisão da saída ----------

class AreaSugeridaSerializer(serializers.Serializer):
    slug = serializers.CharField()
    justificativa = serializers.CharField(max_length=400)
    peso = serializers.IntegerField(min_value=0, max_value=5)


class ConsultorSerializer(serializers.Serializer):
    """As regras do prompt que dá para conferir. Precisa de `slugs` no context."""

    areas = AreaSugeridaSerializer(many=True)
    nenhuma_area_adequada = serializers.BooleanField(default=False)
    nova_area_sugerida = serializers.CharField(max_length=100, allow_blank=True, default="")
    nome_sugerido = serializers.CharField(max_length=150, allow_blank=True, default="")
    descricao_sugerida = serializers.CharField(max_length=1000, allow_blank=True, default="")
    observacoes = serializers.CharField(max_length=500, allow_blank=True, default="")

    def validate_areas(self, areas):
        validas, vistas = [], set()
        for area in areas:
            # Área inventada ou repetida sai da lista; as que existem continuam.
            if area["slug"] in self.context["slugs"] and area["slug"] not in vistas:
                vistas.add(area["slug"])
                validas.append(area)
        if not validas:
            raise serializers.ValidationError("nenhuma área da lista do catálogo")
        return validas[:3]


def saida_valida(texto, contexto):
    serializer = ConsultorSerializer(
        data=ler_json(texto),
        context={"slugs": {area["slug"] for area in contexto["areas"]}},
    )
    if not serializer.is_valid():
        raise LLMInvalidOutput(f"saída recusada: {serializer.errors}")
    return serializer.validated_data


# ---------- Consulta ----------

@dataclass
class Sugestao:
    """O que a tela recebe: a análise da LLM já com os dados do catálogo."""

    areas: list
    nenhuma_area_adequada: bool
    nova_area_sugerida: str
    nome_sugerido: str
    descricao_sugerida: str
    observacoes: str
    semelhantes: list = field(default_factory=list)
    modelo: str = ""
    cache_hit: bool = False


def chave_do_cache(prompt):
    bruto = "|".join([settings.LLM_PROVIDER, settings.LLM_MODEL, "consultor", PROMPT_VERSION, prompt])
    return "llm:consultor:" + hashlib.sha256(bruto.encode("utf-8")).hexdigest()


def _ler_cache(chave):
    """O cache só economiza cota: se ele falhar (tabela sem createcachetable), a consulta segue."""
    try:
        return cache.get(chave)
    except Exception:
        logger.exception("Consultor: cache indisponível na leitura")
        return None


def _gravar_cache(chave, valor):
    try:
        cache.set(chave, valor, timeout=CACHE_SEGUNDOS)
    except Exception:
        logger.exception("Consultor: cache indisponível na gravação")


def consultar(nome, descricao, ignorar_id=None):
    """A sugestão do consultor, ou LLMError / EntradaInvalida com o motivo.

    Não usa a pausa do quiz (LLM_PAUSA): uma falha aqui não pode tirar a IA
    dos alunos. A resposta aprovada fica um dia no cache: o mesmo pedido com o
    mesmo catálogo não gasta cota de novo.
    """
    if not settings.LLM_ENABLED:
        raise LLMUnavailable("a camada de IA está desligada (LLM_ENABLED=0)")
    contexto = montar_contexto(nome, descricao, ignorar_id)
    prompt = montar_prompt(contexto)
    chave = chave_do_cache(prompt)

    guardada = _ler_cache(chave)
    if guardada:
        texto, modelo = guardada["texto"], guardada["modelo"]
    else:
        resposta = get_provider(timeout=settings.LLM_TIMEOUT_CONSULTOR).complete(prompt)
        texto, modelo = resposta.text, resposta.model
    dados = saida_valida(texto, contexto)
    if not guardada:
        _gravar_cache(chave, {"texto": texto, "modelo": modelo})

    por_slug = {area["slug"]: area for area in contexto["areas"]}
    return Sugestao(
        areas=[
            {
                "id": por_slug[item["slug"]]["id"],
                "slug": item["slug"],
                "nome": por_slug[item["slug"]]["nome"],
                "justificativa": item["justificativa"],
                "peso": item["peso"],
                "tem_pesos_no_quiz": por_slug[item["slug"]]["tem_pesos_no_quiz"],
            }
            for item in dados["areas"]
        ],
        nenhuma_area_adequada=dados["nenhuma_area_adequada"],
        nova_area_sugerida=dados["nova_area_sugerida"] if dados["nenhuma_area_adequada"] else "",
        nome_sugerido=dados["nome_sugerido"],
        descricao_sugerida=dados["descricao_sugerida"],
        observacoes=dados["observacoes"],
        semelhantes=[
            {
                "id": curso["id"],
                "nome": curso["nome"],
                "area": por_slug.get(curso["area_principal"], {}).get("nome", curso["area_principal"]),
                "possivel_duplicado": curso["possivel_duplicado"],
            }
            for curso in contexto["semelhantes"]
        ],
        modelo=modelo,
        cache_hit=bool(guardada),
    )
