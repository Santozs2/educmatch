
from collections import Counter
from datetime import timedelta
from django.db.models import Count, Q
from django.utils import timezone
from accounts.models import Interesse
from catalogo.models import Area, Curso
from quiz.models import Peso_alternativa, Recomendacao, Tentativa_de_resposta

PERIODOS = {"30": 30, "90": 90, "365": 365}


def inicio_do_periodo(dias):
    if dias is None:
        return None
    return timezone.now() - timedelta(days=dias)


def _no_periodo(inicio, prefixo="criado_em"):
    if inicio is None:
        return Q()
    return Q(**{f"{prefixo}__gte": inicio})


def total_de_tentativas(inicio):
    return Tentativa_de_resposta.objects.filter(_no_periodo(inicio)).count()


def top_cursos_com_manifestacoes(inicio, limite=3):
    """Top N cursos com mais manifestações (recomendações rank=1 no período)."""
    return list(
        Recomendacao.objects
        .filter(rank=1)
        .filter(_no_periodo(inicio, "tentativa__criado_em"))
        .values("curso_id", "curso__nome_curso")
        .annotate(total=Count("tentativa_id", distinct=True))
        .order_by("-total", "curso__nome_curso")[:limite]
    )


def top_cursos_em_primeiro(inicio, limite=10):
    return list(
        Recomendacao.objects
        .filter(rank=1)
        .filter(_no_periodo(inicio, "tentativa__criado_em"))
        .values("curso_id", "curso__nome_curso")
        .annotate(total=Count("tentativa_id", distinct=True))
        .order_by("-total", "curso__nome_curso")[:limite]
    )


def top_cursos_no_top5(inicio, limite=10):

    return list(
        Recomendacao.objects
        .filter(_no_periodo(inicio, "tentativa__criado_em"))
        .values("curso_id", "curso__nome_curso")
        .annotate(total=Count("tentativa_id", distinct=True))
        .order_by("-total", "curso__nome_curso")[:limite]
    )


def conversao_por_curso(inicio):

    linhas = (
        Curso.objects
        .filter(is_active=True)
        .annotate(
            recomendado=Count(
                "recomendacoes",
                filter=_no_periodo(inicio, "recomendacoes__tentativa__criado_em"),
                distinct=True,
            ),
            interessados=Count(
                "interessados",
                filter=_no_periodo(inicio, "interessados__criado_em"),
                distinct=True,
            ),
        )
        .values("id", "nome_curso", "recomendado", "interessados")
        .order_by("-interessados", "nome_curso")
    )

    resultado = []
    for linha in linhas:
        recomendado = linha["recomendado"]
        linha["taxa"] = (linha["interessados"] / recomendado * 100) if recomendado else None
        resultado.append(linha)
    return resultado


def aderencia_a_recomendacao(inicio):
    base = (
        Interesse.objects
        .filter(_no_periodo(inicio))
        .exclude(rank_snapshot__isnull=True)
    )
    return {
        "com_snapshot": base.count(),
        "por_posicao": list(
            base.values("rank_snapshot")
            .annotate(total=Count("id"))
            .order_by("rank_snapshot")
        ),
        "era_principal": base.filter(era_principal=True).count(),
    }


def demanda_por_area(inicio, limite=12):
    explicacoes = (
        Recomendacao.objects
        .filter(rank=1)
        .filter(_no_periodo(inicio, "tentativa__criado_em"))
        .values_list("explicacao", flat=True)
    )

    contagem = Counter()
    for explicacao in explicacoes:
        if isinstance(explicacao, dict):
            contagem.update(explicacao.keys())

    nomes = dict(Area.objects.values_list("slug", "nome"))
    return [
        {"area": nomes.get(slug, slug), "total": total}
        for slug, total in contagem.most_common(limite)
    ]


def cursos_nunca_recomendados():
    return list(
        Curso.objects
        .filter(is_active=True, recomendacoes__isnull=True)
        .values("id", "nome_curso")
        .order_by("nome_curso")
    )


def distribuicao_de_confianca(inicio):
    return list(
        Tentativa_de_resposta.objects
        .filter(_no_periodo(inicio))
        .values("confidence_level")
        .annotate(total=Count("id"))
        .order_by("confidence_level")
    )


def cursos_ativos():
    return Curso.objects.filter(is_active=True).count()


def cobertura_de_areas():
    return list(
        Area.objects
        .annotate(alternativas=Count("pesos_alternativa", distinct=True))
        .values("slug", "nome", "alternativas")
        .order_by("alternativas", "nome")
    )