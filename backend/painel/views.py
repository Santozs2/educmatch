from django.contrib.admin.views.decorators import staff_member_required
from django.shortcuts import render

from painel import metricas
from painel import privacidade


@staff_member_required
def dashboard(request):
    escolhido = request.GET.get("periodo", "90")
    dias = metricas.PERIODOS.get(escolhido)
    inicio = metricas.inicio_do_periodo(dias)

    total = metricas.total_de_tentativas(inicio)
    tem_massa = privacidade.periodo_tem_massa_suficiente(total)

    contexto = {
        "periodo": escolhido,
        "periodos": metricas.PERIODOS,
        "total_de_tentativas": total,
        "tem_massa": tem_massa,
        "k_minimo": privacidade.K_MINIMO,
    }

    if tem_massa:
        contexto.update({
            "top_primeiro": privacidade.suprimir_pequenos(
                metricas.top_cursos_em_primeiro(inicio)
            ),
            "top_manifestacoes": privacidade.suprimir_pequenos(
                metricas.top_cursos_com_manifestacoes(inicio)
            ),
            "cursos_ativos": metricas.cursos_ativos(),
            "top_cinco": privacidade.suprimir_pequenos(
                metricas.top_cursos_no_top5(inicio)
            ),
            "conversao": privacidade.suprimir_pequenos(
                metricas.conversao_por_curso(inicio), campo="interessados"
            ),
            "aderencia": metricas.aderencia_a_recomendacao(inicio),
            "demanda_por_area": privacidade.suprimir_pequenos(
                metricas.demanda_por_area(inicio)
            ),
            "confianca": metricas.distribuicao_de_confianca(inicio),
            "orfaos": metricas.cursos_nunca_recomendados(),
            "cobertura": metricas.cobertura_de_areas(),
        })

    return render(request, "painel/dashboard.html", contexto)