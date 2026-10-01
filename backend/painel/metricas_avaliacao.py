"""Agregações da avaliação de fim de curso. Mesma regra do metricas.py:
funções puras, sem request, e nenhuma volta uma resposta inteira de alguém.
"""
from collections import Counter

from django.db.models import Count, Q
from django.utils import timezone

from avaliacao.models import ItemDeResposta, LinkDeAvaliacao, Pergunta, RespostaDeAvaliacao


def _desde(inicio, prefixo="respondido_em"):
    # A resposta guarda só o dia: compara com o dia do início do período.
    if inicio is None:
        return Q()
    return Q(**{f"{prefixo}__gte": timezone.localdate(inicio)})


def respostas(inicio, cursos=None):
    """As respostas do período; `cursos` (lista de ids) restringe, None não restringe."""
    filtro = _desde(inicio)
    if cursos is not None:
        filtro &= Q(link__curso_id__in=cursos)
    return RespostaDeAvaliacao.objects.filter(filtro)


def cursos_com_massa(inicio, k):
    """Ids dos cursos com k respostas ou mais no período.

    Só eles entram nas agregações de opinião. Se um curso com 3 respostas
    entrasse no "Todos os cursos", a diferença entre o NPS geral e o NPS dos
    outros cursos (que a tabela mostra) devolveria a opinião daquelas 3 pessoas.
    """
    return list(
        RespostaDeAvaliacao.objects.filter(_desde(inicio))
        .values("link__curso_id")
        .annotate(total=Count("id"))
        .filter(total__gte=k)
        .values_list("link__curso_id", flat=True)
    )


def links(limite=30):
    return list(
        LinkDeAvaliacao.objects
        .annotate(total=Count("respostas"))
        .values("id", "token", "turma", "criado_em", "ativo", "total", "curso__nome_curso")
        .order_by("-criado_em")[:limite]
    )


def nps(notas):
    """% de promotores (9 e 10) menos % de detratores (0 a 6). Vai de -100 a 100."""
    if not notas:
        return None
    promotores = sum(1 for nota in notas if nota >= 9)
    detratores = sum(1 for nota in notas if nota <= 6)
    return round((promotores - detratores) / len(notas) * 100)


def resumo_por_curso(inicio):
    """Por curso avaliado: quantas respostas, NPS e média das escalas."""
    linhas = (
        RespostaDeAvaliacao.objects
        .filter(_desde(inicio))
        .values("link__curso_id", "link__curso__nome_curso")
        .annotate(total=Count("id"))
        .order_by("link__curso__nome_curso")
    )
    itens = ItemDeResposta.objects.filter(_desde(inicio, "resposta__respondido_em"))
    notas, escalas = {}, {}
    for curso_id, tipo, numero in itens.values_list("resposta__link__curso_id", "pergunta__tipo", "numero"):
        if tipo == "nps":
            notas.setdefault(curso_id, []).append(numero)
        elif tipo == "escala":
            escalas.setdefault(curso_id, []).append(numero)

    resultado = []
    for linha in linhas:
        curso_id = linha["link__curso_id"]
        valores = escalas.get(curso_id, [])
        resultado.append({
            "curso_id": curso_id,
            "nome": linha["link__curso__nome_curso"],
            "total": linha["total"],
            "nps": nps(notas.get(curso_id, [])),
            "media": sum(valores) / len(valores) if valores else None,
        })
    return resultado


def por_pergunta(inicio, cursos):
    """Para cada pergunta ativa, o resumo que cabe ao tipo dela, só dos `cursos` dados."""
    filtro = _desde(inicio, "resposta__respondido_em") & Q(resposta__link__curso_id__in=cursos)

    resultado = []
    for pergunta in Pergunta.objects.filter(ativa=True):
        itens = ItemDeResposta.objects.filter(filtro, pergunta=pergunta)
        bloco = {"pergunta": pergunta, "total": itens.count()}

        if pergunta.tipo in ("nps", "escala"):
            numeros = list(itens.values_list("numero", flat=True))
            contagem = Counter(numeros)
            faixa = range(11) if pergunta.tipo == "nps" else range(1, 6)
            bloco["distribuicao"] = [{"rotulo": n, "total": contagem.get(n, 0)} for n in faixa]
            bloco["nps"] = nps(numeros) if pergunta.tipo == "nps" else None
            bloco["media"] = sum(numeros) / len(numeros) if numeros else None
        elif pergunta.tipo == "escolha":
            contagem = Counter(itens.values_list("texto", flat=True))
            bloco["distribuicao"] = [{"rotulo": opcao, "total": contagem.get(opcao, 0)} for opcao in pergunta.opcoes]
        else:
            # Ordem alfabética: na ordem de chegada, o 1º texto seria o de quem respondeu primeiro.
            bloco["textos"] = sorted(t for t in itens.values_list("texto", flat=True) if t)
        resultado.append(bloco)
    return resultado


def linhas_do_csv(inicio, cursos):
    """Uma linha por item (curso, pergunta, resposta), ordenadas por pergunta e valor.

    Sem turma, sem data e sem id da resposta: as linhas de uma mesma pessoa não
    podem ser juntadas de volta numa resposta completa.
    """
    filtro = _desde(inicio, "resposta__respondido_em") & Q(resposta__link__curso_id__in=cursos)
    linhas = sorted(
        ItemDeResposta.objects.filter(filtro)
        .values_list("resposta__link__curso__nome_curso", "pergunta__ordem", "numero", "texto", "pergunta__texto"),
        key=lambda linha: (linha[0], linha[1], linha[2] if linha[2] is not None else -1, linha[3]),
    )
    return [
        (curso, pergunta, str(numero) if numero is not None else texto)
        for curso, _, numero, texto, pergunta in linhas
    ]