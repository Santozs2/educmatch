import math 
from collections import defaultdict
from django.conf import settings 
from django.db import transaction
from catalogo.models import Area, Curso
from quiz.models import Recomendacao

TOP3 = 3
CORTE_MINIMO = 0.5
CORTE_MAXIMO = 0.8

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
    if afinidade < CORTE_MINIMO:
        return "baixo"
    elif afinidade < CORTE_MAXIMO:
        return "medio"
    else:
        return "alto"


def confianca(ranking):
    if not ranking:
        return "baixa"

    primeiro = ranking[0][1]
    segundo = ranking[1][1] if len(ranking) > 1 else 0.0

    if primeiro <= 0:
        return "baixa"

    separacao = (primeiro - segundo) / primeiro
    if separacao >= 0.15:
        return "alta"
    if separacao >= 0.05:
        return "media"
    return "baixa"


@transaction.atomic
def recomedacao(tentativa, limit=None):
    if limit is None:
        limit = settings.QUIZ_RECOMENDACAO_LIMIT
    alternativas = [resposta.alternativa for resposta in tentativa.respostas.select_related("alternativa")]
    perfil = perfil_vetor(alternativas)
    nome_areas = dict(Area.objects.values_list("slug", "nome"))
    ranking = rank_cursos(perfil, Curso.objects.all(), nome_areas)[:limit]

    primeiro = ranking[0][1] if ranking else 0.0
    segundo = ranking[1][1] if len(ranking) > 1 else 0.0

    tentativa.diferenca = primeiro - segundo
    tentativa.confidence_band = confianca(ranking)
    tentativa.save(update_fields=["confidence_band", "diferenca"])

    tentativa.recomendacoes.all().delete()
    return Recomendacao.objects.bulk_create(
        [
            Recomendacao(
                tentativa=tentativa,
                curso=curso,
                score=round(score, 4),
                rank=posicao,
                explicacao=explicacao,
            )
            for posicao, (curso, score, explicacao) in enumerate(ranking, start=1)
        ]
    )