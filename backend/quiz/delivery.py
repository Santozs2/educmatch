import hashlib
import logging
import time
from dataclasses import asdict, replace

from django.conf import settings
from django.core.cache import cache
from django.db import transaction

from quiz.engine import TOP3, perfil_vetor
from quiz.llm import LLMError, LLMResponse, get_provider
from quiz.models import Recomendacao
from quiz.prompt import montar_prompt
from quiz.serializers import Entrega, validate_delivery

logger = logging.getLogger(__name__)


def build_payload(attempt):
    """O JSON de entrada do contrato. Não leva nome, e-mail nem usuário."""
    respostas = list(
        attempt.respostas.select_related("alternativa").prefetch_related("alternativa__pesos__area")
    )
    perfil = perfil_vetor([resposta.alternativa for resposta in respostas])
    nomes = {}
    for resposta in respostas:
        for peso in resposta.alternativa.pesos.all():
            nomes[peso.area.slug] = peso.area.nome
    fortes = sorted(perfil.items(), key=lambda item: item[1], reverse=True)[:TOP3]

    recomendacoes = attempt.recomendacoes.select_related("curso").order_by("rank_engine")
    return {
        "perfil": {
            "areas_fortes": [
                {"area": slug, "area_name": nomes[slug], "pontuacao": round(valor, 2)}
                for slug, valor in fortes
                if valor > 0
            ]
        },
        "candidatos": [
            {
                "course_id": rec.curso_id,
                "nome": rec.curso.nome_curso,
                "descricao": rec.curso.descricao,
                "score": round(rec.score, 4),
                "rank_engine": rec.rank_engine,
                "top_areas": [
                    {"area_name": area.get("area_name"), "percentual": area.get("percentual")}
                    for area in (rec.explicacao or {}).get("top_areas", [])
                ],
            }
            for rec in recomendacoes
        ],
        # Regra 2 do prompt: só estes ids podem ir para o 1º lugar.
        "tie_set": list(attempt.tie_set),
    }


def chave_do_cache(prompt):
    """Mesmo provedor, modelo, versão e prompt = mesma chave. O prompt já traz o perfil."""
    bruto = "|".join([settings.LLM_PROVIDER, settings.LLM_MODEL, settings.LLM_PROMPT_VERSION, prompt])
    return "llm:" + hashlib.sha256(bruto.encode("utf-8")).hexdigest()


def deliver(attempt) -> Entrega | None:
    """A entrega da LLM, já revisada. Com a IA desligada, não chama nada.

    Saída fora do contrato vira LLMInvalidOutput: nada inválido sai daqui.
    Só resposta aprovada entra no cache; no acerto, não há tokens gastos.
    """
    if not settings.LLM_ENABLED:
        return None
    payload = build_payload(attempt)
    if not payload["candidatos"]:
        return None
    prompt = montar_prompt(payload, settings.LLM_PROMPT_VERSION)
    chave = chave_do_cache(prompt)

    guardada = cache.get(chave)
    resposta = LLMResponse(**guardada) if guardada else get_provider().complete(prompt)
    entrega = validate_delivery(resposta.text, payload)
    if not guardada:
        cache.set(chave, asdict(resposta), timeout=None)  # não expira: é a resposta da banca
    return replace(
        entrega,
        modelo=resposta.model,
        tokens_in=None if guardada else resposta.tokens_in,
        tokens_out=None if guardada else resposta.tokens_out,
        cache_hit=bool(guardada),
    )


def entregar(attempt) -> bool:
    """Passo 9: grava a entrega da LLM ou, em qualquer falha, a ordem da engine.

    Nunca levanta exceção: a engine já gravou o resultado antes, e é ele que o
    aluno vê se a LLM falhar. Devolve True quando o texto da LLM foi gravado.
    """
    if not settings.LLM_ENABLED:
        return False
    inicio = time.monotonic()
    try:
        entrega = deliver(attempt)
    except LLMError as erro:
        logger.warning("LLM no fallback (tentativa %s): %s", attempt.pk, erro)
        entrega, falhou = None, True
    except Exception:  # um bug nosso também não pode virar erro 500 no quiz
        logger.exception("Erro inesperado na camada de IA (tentativa %s)", attempt.pk)
        entrega, falhou = None, True
    else:
        if entrega is None:
            return False  # sem candidatos: não houve chamada
        falhou = False

    _gravar(attempt, entrega, latencia_ms=round((time.monotonic() - inicio) * 1000))
    return not falhou


@transaction.atomic
def _gravar(attempt, entrega, latencia_ms):
    recomendacoes = list(attempt.recomendacoes.order_by("rank_engine"))
    if entrega is None:
        for rec in recomendacoes:
            rec.rank_final, rec.llm_text = rec.rank_engine, ""
    else:
        posicao = {curso_id: i for i, curso_id in enumerate(entrega.ordem, start=1)}
        for rec in recomendacoes:
            rec.rank_final, rec.llm_text = posicao[rec.curso_id], entrega.textos[rec.curso_id]
    Recomendacao.objects.bulk_update(recomendacoes, ["rank_final", "llm_text"])

    metadados = {
        "llm_model": (entrega.modelo if entrega else settings.LLM_MODEL or settings.LLM_PROVIDER)[:60],
        "prompt_version": settings.LLM_PROMPT_VERSION[:20],
        "latency_ms": latencia_ms,
        "tokens_in": entrega.tokens_in if entrega else None,
        "tokens_out": entrega.tokens_out if entrega else None,
        "used_fallback": entrega is None,
        # Medido pelo servidor, não declarado pela LLM: o 1º entregue é o 1º da engine?
        "diverged": bool(entrega) and entrega.ordem[0] != recomendacoes[0].curso_id,
        "cache_hit": bool(entrega) and entrega.cache_hit,
    }
    for campo, valor in metadados.items():
        setattr(attempt, campo, valor)
    attempt.save(update_fields=list(metadados))
