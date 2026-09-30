import math 
from collections import defaultdict
from django.conf import settings 
from django.db import transaction
from catalogo.models import Area, Curso
from quiz.models import Recomendacao

TOP3 = 3
CORTE_MINIMO = 0.5
CORTE_MAXIMO = 0.8
# Diferença ABSOLUTA de afinidade entre dois cursos. A mesma régua decide a
# banda de confiança, o tie_set e a regra 2 do prompt (quando a LLM pode
# trocar o 1º lugar): três lugares, um número só.
EMPATE = 0.05
BANDA_CONFIANCA_ALTA = 0.15
CASAS = 6  # arredonda antes de comparar: 0.80 - 0.75 dá 0.05000000000000004

def vetor_curso(curso):
    vetor = {
        peso.area.slug: peso.peso
        for peso in curso.curso_peso.all()
        if peso.area is not None and hasattr(peso.area, "slug") 
    }
    if not vetor and curso.area_principal:
        vetor[curso.area_principal.slug] = 1.0
    return vetor

def perfil_vetor(alternativas):
    vetor = defaultdict(float)
    for alternativa in alternativas:
        for peso in alternativa.pesos.all():
            vetor[peso.area.slug] += peso.peso
    return dict(vetor)

def dot(a,b):
    return sum(valor * b.get(slug, 0.0) for slug, valor in a.items())

def norm(vetor):
    return math.sqrt(sum(valor * valor for valor in vetor.values()))

def afinidade(a, b):
    denominador = norm(a) * norm(b)
    if not denominador:
        return 0.0
    return dot(a, b) / denominador

def explicacao(profile, vetor_curso, nome_areas):
    contribuicoes = {
        slug: valor * vetor_curso[slug]
        for slug, valor in profile.items()
        if slug in vetor_curso
    }
    total = sum(contribuicoes.values())
    maiores = sorted(contribuicoes.items(), key=lambda item: item[1], reverse=True)[:TOP3]
    return {
        "top_areas": [
            {
                "area": slug,
                "area_name": nome_areas.get(slug, slug),
                "area_nome": nome_areas.get(slug, slug),
                "contribuicao": round(valor, 2),
                "percentual": round(valor / total * 100, 1) if total else 0.0,
            }
            for slug, valor in maiores
        ]
    }
    
def rank_cursos(profile, cursos, nome_areas):
    resultado = [
        (curso, afinidade(profile, vetor), explicacao(profile, vetor, nome_areas))
        for curso, vetor in ((c, vetor_curso(c)) for c in cursos)
    ]
    resultado = sorted(resultado, key=lambda item: item[1], reverse=True)
    return resultado

def banda(afinidade):
    """Nível da afinidade de UM curso: baixo (< 0,5), medio (< 0,8) ou alto.

    Não confundir com confianca(), que mede a separação entre o 1º e o 2º.
    Fica no motor para o fallback e para o tom do prompt: um 1º lugar com
    afinidade "baixo" não pode ser apresentado como "combina muito com você",
    venha o texto da LLM ou da engine.
    """
    if afinidade < CORTE_MINIMO:
        return "baixo"
    elif afinidade < CORTE_MAXIMO:
        return "medio"
    else:
        return "alto"


def diferenca_do_topo(ranking, score):
    return round(ranking[0][1] - score, CASAS)


def confianca(ranking):
    """Quanto o 1º lugar se separou do 2º, no ranking INTEIRO (antes do corte)."""
    if not ranking or ranking[0][1] <= 0:
        return "baixa"

    segundo = ranking[1][1] if len(ranking) > 1 else 0.0
    diferenca = diferenca_do_topo(ranking, segundo)
    if diferenca >= BANDA_CONFIANCA_ALTA:
        return "alta"
    if diferenca >= EMPATE:
        return "media"
    return "baixa"


def conjunto_de_empate(ranking):
    """Ids dos cursos a menos de EMPATE do 1º lugar, o 1º incluído.

    É a lista de quem a LLM pode colocar em 1º (regra 2). Um item só = sem
    empate: a LLM não pode trocar o principal.
    """
    if not ranking:
        return []
    return [curso.pk for curso, score, _ in ranking if diferenca_do_topo(ranking, score) < EMPATE]

@transaction.atomic
def recomendar(tentativa, limit=None):
    if limit is None:
        limit = settings.QUIZ_RECOMENDACAO_LIMIT
    respostas = (
        tentativa.respostas
        .select_related("alternativa")                 # FK: um JOIN
        .prefetch_related("alternativa__pesos__area")  # para-muitos: uma consulta a mais
    )
    perfil = perfil_vetor([resposta.alternativa for resposta in respostas])
    nome_areas = dict(Area.objects.values_list("slug", "nome"))

    # REC-02: curso desativado não entra no cálculo (e nem no painel).
    cursos = Curso.objects.filter(is_active=True).prefetch_related("curso_peso__area")
    ranking = rank_cursos(perfil, cursos, nome_areas)   # completo

    primeiro = ranking[0][1] if ranking else 0.0
    segundo = ranking[1][1] if len(ranking) > 1 else 0.0

    tentativa.diferenca = primeiro - segundo
    tentativa.confidence_band = confianca(ranking)     # REC-04: mede antes do corte
    ranking = ranking[:limit]
    tentativa.tie_set = conjunto_de_empate(ranking)    # só quem a LLM vai receber
    tentativa.save(update_fields=["confidence_band", "diferenca", "tie_set"])

    Recomendacao.objects.filter(tentativa=tentativa).delete()
    Recomendacao.objects.bulk_create(
        [
            Recomendacao(
                tentativa=tentativa,
                curso=curso,
                score=score,
                rank_engine=rank,
                rank_final=rank, #Sem LLM, a ordem entregue e da engine.
                explicacao=explicacao,
            )
            for rank, (curso, score, explicacao) in enumerate(ranking, start=1)
        ]
    )
    return tentativa