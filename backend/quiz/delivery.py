import json

from django.conf import settings

from quiz.engine import TOP3, perfil_vetor
from quiz.llm import LLMResponse, get_provider


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


def deliver(attempt) -> LLMResponse | None:
    """Chama a LLM para esta tentativa. Com a IA desligada, não chama nada."""
    if not settings.LLM_ENABLED:
        return None
    payload = build_payload(attempt)
    if not payload["candidatos"]:
        return None
    # Provisório, até que o contrato seja definido: o prompt é o JSON, e a saída é o JSON.
    prompt = json.dumps(payload, ensure_ascii=False, sort_keys=True)
    return get_provider().complete(prompt)