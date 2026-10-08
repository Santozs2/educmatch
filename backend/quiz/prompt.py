"""O prompt padrão da camada de IA: um arquivo .md por versão, nunca string no código.

A versão vem de LLM_PROMPT_VERSION e é gravada em cada tentativa (Passo 9).
Uma versão já usada não se edita: muda o texto, nasce entrega_v2.md.
"""
import json
import re
from functools import lru_cache
from pathlib import Path

from quiz.llm import LLMUnavailable

PASTA = Path(__file__).resolve().parent / "prompts"


@lru_cache
def carregar(versao):
    if not re.fullmatch(r"[\w.-]+", versao):
        raise LLMUnavailable(f"versão de prompt inválida: {versao!r}")
    try:
        return (PASTA / f"entrega_{versao}.md").read_text(encoding="utf-8")
    except FileNotFoundError:
        raise LLMUnavailable(f"não existe prompt para a versão {versao!r}") from None


def _json(valor):
    return json.dumps(valor, ensure_ascii=False, indent=2)


def montar_prompt(payload, versao):
    """O texto da versão pedida, com os dados desta tentativa no bloco DADOS."""
    return (
        carregar(versao)
        .replace("{{PERFIL_JSON}}", _json(payload["perfil"]))
        .replace("{{CANDIDATOS_JSON}}", _json(payload["candidatos"]))
        .replace("{{TIE_SET_JSON}}", _json(payload["tie_set"]))
    )