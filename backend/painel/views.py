from urllib.parse import urlencode

from django.contrib.admin.views.decorators import staff_member_required
from django.shortcuts import redirect, render
from django.urls import reverse
from django.views.decorators.http import require_POST

from painel import metricas, privacidade
from quiz.models import QuestionarioLink, Tentativa_de_resposta


def _links_ativos(request):
    return [
        {
            "url": request.build_absolute_uri(
                reverse("questionario-link", kwargs={"token": link.token})
            ),
            "criado_em": link.criado_em,
        }
        for link in QuestionarioLink.objects.filter(ativo=True)[:5]
    ]


def _contexto_base(request, secao):
    """O que toda tela do painel usa: período escolhido, massa mínima e menu."""
    escolhido = request.GET.get("periodo", "mensal")
    if escolhido not in metricas.PERIODOS:
        escolhido = "mensal"
    mes = request.GET.get("mes") or ""
    inicio = metricas.inicio_do_periodo(escolhido, mes=mes)
    total = metricas.total_de_tentativas(inicio)

    filtro = {"periodo": escolhido}
    if escolhido == "mes" and mes:
        filtro["mes"] = mes

    return inicio, {
        "secao": secao,
        "periodo": escolhido,
        "periodo_label": metricas.PERIODOS[escolhido]["label"],
        "mes": mes,
        "periodos": metricas.PERIODOS,
        # Os links do menu levam o período junto: trocar de tela não reseta o filtro.
        "periodo_qs": urlencode(filtro),
        "total_de_tentativas": total,
        "tem_massa": privacidade.periodo_tem_massa_suficiente(total),
        "k_minimo": privacidade.K_MINIMO,
    }


@staff_member_required
def dashboard(request):
    inicio, contexto = _contexto_base(request, "inicio")
    contexto["links"] = _links_ativos(request)
    contexto["cursos_ativos"] = metricas.cursos_ativos()
    if not contexto["tem_massa"]:
        # Período pequeno: nenhum número além do total sai do servidor.
        return render(request, "painel/inicio.html", contexto)

    sup = privacidade.suprimir_pequenos
    contexto.update({
        "via_link": metricas.tentativas_via_link(inicio),
        "conversao_geral": metricas.conversao_geral(inicio),
        "serie": sup(metricas.tentativas_por_dia(inicio)),
        "demanda_por_area": sup(metricas.demanda_por_area(inicio)),
        "atividade": sup(metricas.atividade_recente()),
    })
    return render(request, "painel/inicio.html", contexto)


@staff_member_required
def quiz_visao_geral(request):
    inicio, contexto = _contexto_base(request, "quiz")
    if not contexto["tem_massa"]:
        return render(request, "painel/quiz.html", contexto)

    sup = privacidade.suprimir_pequenos
    conversao = sup(metricas.conversao_por_curso(inicio), campo="interessados")
    for linha in conversao:
        if linha.get("suprimido"):
            # taxa x recomendado / 100 devolveria o número que acabou de ser escondido
            linha["taxa"] = None

    aderencia = metricas.aderencia_a_recomendacao(inicio)
    aderencia["por_posicao"] = sup(aderencia["por_posicao"])
    # Mesma regra da conversão: a taxa sobre um total conhecido devolveria o número pequeno.
    principal = aderencia["era_principal"]
    aderencia["taxa"] = (
        principal / aderencia["com_snapshot"] * 100 if principal >= privacidade.K_MINIMO else None
    )

    confianca = sup(metricas.distribuicao_de_confianca(inicio))
    nomes = dict(Tentativa_de_resposta.CONFIDENCE_CHOICE_NIVEIS)
    for linha in confianca:
        linha["rotulo"] = nomes.get(linha["confidence_band"], "Sem banda")

    contexto.update({
        "top_manifestacoes": sup(metricas.top_cursos_com_manifestacoes(inicio)),
        "top_primeiro": sup(metricas.top_cursos_em_primeiro(inicio, limite=5)),
        "top_cinco": sup(metricas.top_cursos_no_top5(inicio, limite=5)),
        "confianca": confianca,
        "aderencia": aderencia,
        "conversao": conversao,
        "orfaos": metricas.cursos_nunca_recomendados(),
        "cobertura": metricas.cobertura_de_areas(),
    })
    return render(request, "painel/quiz.html", contexto)


@require_POST
@staff_member_required
def fechar_link(request):
    ativo = QuestionarioLink.objects.filter(ativo=True)
    for link in ativo:
        link.ativo = False
        link.save()
    return redirect("painel-dashboard")


@require_POST
@staff_member_required
def gerar_link(request):
    QuestionarioLink.objects.create(criado_por=request.user)
    return redirect("painel-dashboard")
