from django.contrib.admin.views.decorators import staff_member_required
from django.shortcuts import redirect, render
from django.urls import reverse
from django.views.decorators.http import require_POST

from painel import metricas, privacidade
from quiz.models import QuestionarioLink


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


@staff_member_required
def dashboard(request):
    escolhido = request.GET.get("periodo", "90")
    dias = metricas.PERIODOS.get(escolhido)  # "tudo" ou chave inválida -> None -> sem filtro
    inicio = metricas.inicio_do_periodo(dias)

    total = metricas.total_de_tentativas(inicio)
    tem_massa = privacidade.periodo_tem_massa_suficiente(total)

    contexto = {
        "periodo": escolhido,
        "periodos": metricas.PERIODOS,
        "total_de_tentativas": total,
        "tem_massa": tem_massa,
        "k_minimo": privacidade.K_MINIMO,
        "links": _links_ativos(request),
    }
    if not tem_massa:
        # Período pequeno: nenhum número além do total sai do servidor.
        return render(request, "painel/dashboard.html", contexto)

    sup = privacidade.suprimir_pequenos

    conversao = sup(metricas.conversao_por_curso(inicio), campo="interessados")
    for linha in conversao:
        if linha.get("suprimido"):
            # taxa x recomendado / 100 devolveria o número que acabou de ser escondido
            linha["taxa"] = None

    aderencia = metricas.aderencia_a_recomendacao(inicio)
    aderencia["por_posicao"] = sup(aderencia["por_posicao"])

    contexto.update({
        "cursos_ativos": metricas.cursos_ativos(),
        "via_link": metricas.tentativas_via_link(inicio),
        "top_primeiro": sup(metricas.top_cursos_em_primeiro(inicio)),
        "top_manifestacoes": sup(metricas.top_cursos_com_manifestacoes(inicio)),
        "top_cinco": sup(metricas.top_cursos_no_top5(inicio)),
        "conversao": conversao,
        "aderencia": aderencia,
        "demanda_por_area": sup(metricas.demanda_por_area(inicio)),
        "confianca": sup(metricas.distribuicao_de_confianca(inicio)),
        "orfaos": metricas.cursos_nunca_recomendados(),
        "cobertura": metricas.cobertura_de_areas(),
    })
    return render(request, "painel/dashboard.html", contexto)


@require_POST
@staff_member_required
def gerar_link(request):
    QuestionarioLink.objects.create(criado_por=request.user)
    return redirect("painel-dashboard")