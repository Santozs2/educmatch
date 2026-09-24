"""Agregações do painel. Funções puras: recebem datas, devolvem dados.

Nenhuma função daqui recebe request nem usuário, e nenhuma lê `user` ou
`respondido_por`. É isso que garante que o painel fala de cursos e demanda,
nunca de pessoas, e é o que deixa estes números testáveis sem navegador.
"""
from collections import Counter
from datetime import datetime, timedelta

from django.db.models import Count, F, Q
from django.utils import timezone

from accounts.models import Interesse
from catalogo.models import Area, Curso
from quiz.models import Recomendacao, Tentativa_de_resposta

PERIODOS = {
    "diario": {"label": "Diário", "dias": 1},
    "mensal": {"label": "Mensal", "dias": 30},
    "anual": {"label": "Anual", "dias": 365},
    "mes": {"label": "Mês", "dias": None},
}


def _inicio_do_mes(mes):
    if not mes:
        return None
    try:
        inicio = datetime.strptime(mes, "%Y-%m")
    except ValueError:
        return None
    return timezone.make_aware(inicio.replace(day=1, hour=0, minute=0, second=0, microsecond=0))


def inicio_do_periodo(periodo, mes=None):
    if periodo == "mes":
        return _inicio_do_mes(mes)

    config = PERIODOS.get(periodo, PERIODOS["mensal"])
    dias = config.get("dias")
    if dias is None:
        return None
    return timezone.now() - timedelta(days=dias)


def _no_periodo(inicio, prefixo="criado_em"):
    if inicio is None:
        return Q()
    return Q(**{f"{prefixo}__gte": inicio})


def total_de_tentativas(inicio):
    return Tentativa_de_resposta.objects.filter(_no_periodo(inicio)).count()


def tentativas_via_link(inicio):
    """Quantas tentativas do período vieram de um link de questionário."""
    return Tentativa_de_resposta.objects.filter(
        _no_periodo(inicio), questionario_link__isnull=False
    ).count()


def top_cursos_com_manifestacoes(inicio, limite=3):
    """Cursos que mais foram salvos na lista de interesse (C4)."""
    return list(
        Interesse.objects
        .filter(_no_periodo(inicio))
        .values("curso_id", nome=F("curso__nome_curso"))
        .annotate(total=Count("id"))
        .order_by("-total", "nome")[:limite]
    )


def top_cursos_em_primeiro(inicio, limite=10):
    return list(
        Recomendacao.objects
        .filter(rank=1)
        .filter(_no_periodo(inicio, "tentativa__criado_em"))
        .values("curso_id", nome=F("curso__nome_curso"))
        .annotate(total=Count("tentativa_id", distinct=True))
        .order_by("-total", "nome")[:limite]
    )


def top_cursos_no_top5(inicio, limite=10):
    return list(
        Recomendacao.objects
        .filter(_no_periodo(inicio, "tentativa__criado_em"))
        .values("curso_id", nome=F("curso__nome_curso"))
        .annotate(total=Count("tentativa_id", distinct=True))
        .order_by("-total", "nome")[:limite]
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
            # "interessados" já é o related_name de Interesse.curso: anotar com
            # esse nome dá ValueError. O nome curto volta no dicionário abaixo.
            n_interessados=Count(
                "interessados",
                filter=_no_periodo(inicio, "interessados__criado_em"),
                distinct=True,
            ),
        )
        .values("id", "nome_curso", "recomendado", "n_interessados")
        .order_by("-n_interessados", "nome_curso")
    )

    resultado = []
    for linha in linhas:
        linha["interessados"] = linha.pop("n_interessados")
        recomendado = linha["recomendado"]
        linha["taxa"] = (linha["interessados"] / recomendado * 100) if recomendado else None
        resultado.append(linha)
    return resultado


def aderencia_a_recomendacao(inicio):
    """Quando o aluno salva um curso, em que posição do ranking ele estava?"""
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
    """A área que mais pesou em cada 1º lugar do período."""
    explicacoes = (
        Recomendacao.objects
        .filter(rank=1)
        .filter(_no_periodo(inicio, "tentativa__criado_em"))
        .values_list("explicacao", flat=True)
    )

    contagem = Counter()
    for explicacao in explicacoes:
        areas = (explicacao or {}).get("top_areas") or []
        if areas and isinstance(areas[0], dict) and areas[0].get("area"):
            contagem[areas[0]["area"]] += 1

    nomes = dict(Area.objects.values_list("slug", "nome"))
    return [
        {"area": slug, "nome": nomes.get(slug, slug), "total": total}
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
        .values("confidence_band")
        .annotate(total=Count("id"))
        .order_by("confidence_band")
    )


def cursos_ativos():
    return Curso.objects.filter(is_active=True).count()


def cobertura_de_areas():
    """Quantas alternativas do quiz pesam em cada área. Zero = área que o quiz não mede."""
    return list(
        Area.objects
        .annotate(alternativas=Count("pesos__alternativa", distinct=True))
        .values("slug", "nome", "alternativas")
        .order_by("alternativas", "nome")
    )