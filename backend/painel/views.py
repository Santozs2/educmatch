import csv
from urllib.parse import urlencode
from django.contrib import messages
from django.contrib.admin.views.decorators import staff_member_required
from django.db import transaction
from django.http import HttpResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.views.decorators.http import require_POST
from avaliacao.models import LinkDeAvaliacao
from catalogo.models import Area, Curso
from painel import metricas, metricas_avaliacao, privacidade
from painel.forms import NovoCurso, NovoLinkDeAvaliacao, PesosCursoFormSet, NovaArea
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

    link_ativo = QuestionarioLink.objects.filter(ativo=True).order_by("-criado_em").first()
    url_do_quiz = (
        request.build_absolute_uri(reverse("questionario-link", kwargs={"token": link_ativo.token}))
        if link_ativo is not None
        else request.build_absolute_uri(reverse("quiz-inicio"))
    )

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
        "url_do_quiz": url_do_quiz,
    }


@staff_member_required
def dashboard(request):
    inicio, contexto = _contexto_base(request, "inicio")
    contexto["links"] = _links_ativos(request)
    contexto["cursos_ativos"] = metricas.cursos_ativos()
    contexto["avaliacoes_no_periodo"] = metricas_avaliacao.respostas(inicio).count()
    contexto["questoes_ativas"] = metricas.questoes_ativas()
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
        principal / aderencia["com_snapshot"] * 100
        if aderencia["com_snapshot"] and principal >= privacidade.K_MINIMO
        else None
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
        "taxa_de_conclusao": metricas.taxa_de_conclusao(inicio),
        "tempo_tipico": metricas.tempo_tipico(inicio),
        "orfaos": metricas.cursos_nunca_recomendados(),
        "cobertura": metricas.cobertura_de_areas(),
        "camada_de_ia": metricas.camada_de_ia(inicio),
    })
    return render(request, "painel/quiz.html", contexto)

@staff_member_required
def cursos(request):
    form = NovoCurso(request.POST or None)
    pesos_formset = PesosCursoFormSet(request.POST or None)
    if request.method == "POST":
        curso_valido = form.is_valid()
        pesos_validos = pesos_formset.is_valid()
        if curso_valido and pesos_validos:
            with transaction.atomic():
                curso = form.save()
                pesos_formset.instance = curso
                pesos_formset.save()
            messages.success(request, f"Curso {curso.nome_curso} criado com sucesso.")
            return redirect("painel-cursos")
        messages.error(request, "Revise os campos destacados antes de salvar o curso.")

    return _render_cursos(request, curso_form=form, pesos_formset=pesos_formset)


@require_POST
@staff_member_required
def editar_curso(request, pk):
    curso = get_object_or_404(Curso, pk=pk)
    prefixo = f"curso_peso-{curso.pk}"
    form = NovoCurso(request.POST, instance=curso, auto_id=f"curso-{curso.pk}-%s")
    pesos_formset = PesosCursoFormSet(
        request.POST,
        instance=curso,
        prefix=prefixo,
        auto_id=f"{prefixo}-%s",
    )
    curso_valido = form.is_valid()
    pesos_validos = pesos_formset.is_valid()
    if curso_valido and pesos_validos:
        with transaction.atomic():
            curso = form.save()
            pesos_formset.instance = curso
            pesos_formset.save()
        messages.success(request, f"Curso {curso.nome_curso} atualizado com sucesso.")
        return redirect("painel-cursos")

    messages.error(request, "Revise os campos destacados antes de salvar o curso.")
    return _render_cursos(
        request,
        curso_em_edicao=curso,
        form_edicao=form,
        pesos_edicao=pesos_formset,
    )


@require_POST
@staff_member_required
def criar_area(request):
    form = NovaArea(request.POST)
    if form.is_valid():
        area = form.save()
        messages.success(request, f"Área {area.nome} criada com sucesso.")
        return redirect("painel-cursos")

    messages.error(request, "Revise os campos destacados antes de salvar a área.")
    return _render_cursos(request, area_form=form)


@require_POST
@staff_member_required
def remover_curso(request, pk):
    curso = get_object_or_404(Curso, pk=pk)
    curso.is_active = False
    curso.save(update_fields=["is_active"])
    messages.success(request, f"Curso {curso.nome_curso} removido do catálogo ativo.")
    return redirect("painel-cursos")


def _render_cursos(
    request,
    curso_form=None,
    pesos_formset=None,
    curso_em_edicao=None,
    form_edicao=None,
    pesos_edicao=None,
    area_form=None,
):
    inicio, contexto = _contexto_base(request, "cursos")
    inicio = None
    contexto["sem_filtro_periodo"] = True
    total_historico = metricas.total_de_tentativas(inicio)
    contexto["total_de_tentativas"] = total_historico
    contexto["tem_massa"] = privacidade.periodo_tem_massa_suficiente(total_historico)
    linhas = metricas.desempenho_por_curso(inicio)
    if contexto["tem_massa"]:
        linhas = privacidade.suprimir_campos(linhas, ("em_primeiro", "no_top5"))
        contexto["demanda_por_area"] = privacidade.suprimir_pequenos(metricas.demanda_por_area(inicio))
    else:
        for linha in linhas:
            linha["em_primeiro"] = linha["no_top5"] = None

    cursos = Curso.objects.filter(pk__in=[linha["id"] for linha in linhas]).prefetch_related("curso_peso")
    cursos_edicao = []
    for curso in cursos:
        pendente = curso_em_edicao is not None and curso.pk == curso_em_edicao.pk
        prefixo = f"curso_peso-{curso.pk}"
        cursos_edicao.append({
            "curso": curso,
            "modal_id": f"painel-editar-curso-{curso.pk}",
            "form_action": reverse("painel-editar-curso", args=[curso.pk]),
            "aberto": pendente,
            "form": form_edicao if pendente else NovoCurso(
                instance=curso,
                auto_id=f"curso-{curso.pk}-%s",
            ),
            "pesos_formset": pesos_edicao if pendente else PesosCursoFormSet(
                instance=curso,
                prefix=prefixo,
                auto_id=f"{prefixo}-%s",
            ),
        })

    contexto.update({
        "cursos": linhas,
        "curso_form": curso_form or NovoCurso(),
        "pesos_formset": pesos_formset or PesosCursoFormSet(),
        "curso_form_action": reverse("painel-cursos"),
        "criar_modal_aberto": bool(
            curso_form and (curso_form.errors or pesos_formset.errors)
        ),
        "cursos_edicao": cursos_edicao,
        "areas": Area.objects.all(),
        "area_form": area_form or NovaArea(),
        "area_form_action": reverse("painel-criar-area"),
        "area_modal_aberto": bool(area_form and area_form.errors),
    })
    return render(request, "painel/cursos.html", contexto)


@staff_member_required
def links(request):
    _, contexto = _contexto_base(request, "links")
    contexto["sem_filtro_periodo"] = True
    linhas = privacidade.suprimir_pequenos(metricas.testes_por_link())
    for linha in linhas:
        linha["url"] = request.build_absolute_uri(
            reverse("questionario-link", kwargs={"token": linha["token"]})
        )
    contexto["links"] = linhas
    return render(request, "painel/links.html", contexto)


@staff_member_required
def interesse(request):
    inicio, contexto = _contexto_base(request, "interesse")
    if not contexto["tem_massa"]:
        return render(request, "painel/interesse.html", contexto)

    linhas = privacidade.suprimir_campos(
        metricas.interesse_por_curso(inicio), ("total", "contatados", "principal")
    )
    for linha in linhas:
        # O % sobre um total conhecido devolveria um número escondido: só sai se os dois saíram.
        pode = linha["total"] is not None and linha["principal"] is not None
        linha["taxa_principal"] = linha["principal"] / linha["total"] * 100 if pode else None

    contexto.update({
        "funil": privacidade.suprimir_pequenos(metricas.funil_de_interesse(inicio)),
        "por_curso": linhas,
    })
    return render(request, "painel/interesse.html", contexto)


# As ações de link voltam para a tela de onde vieram, mas só para uma destas.
VOLTAS_PERMITIDAS = {"painel-dashboard", "painel-links"}


def _voltar(request):
    destino = request.POST.get("voltar")
    return redirect(destino if destino in VOLTAS_PERMITIDAS else "painel-dashboard")


@require_POST
@staff_member_required
def fechar_um_link(request, pk):
    link = get_object_or_404(QuestionarioLink, pk=pk)
    link.ativo = False
    link.save()
    return _voltar(request)


@require_POST
@staff_member_required
def fechar_link(request):
    ativo = QuestionarioLink.objects.filter(ativo=True)
    for link in ativo:
        link.ativo = False
        link.save()
    return _voltar(request)


@require_POST
@staff_member_required
def gerar_link(request):
    QuestionarioLink.objects.create(criado_por=request.user)
    return _voltar(request)


# ---------- Avaliação de fim de curso (Etapa 5) ----------
# A massa mínima aqui é de RESPOSTAS DE AVALIAÇÃO, e não de testes do quiz:
# um curso com 3 avaliações não pode mostrar média, mesmo num mês de 200 testes.


@staff_member_required
def avaliacoes(request):
    _, contexto = _contexto_base(request, "avaliacoes")
    contexto["sem_filtro_periodo"] = True
    linhas = privacidade.suprimir_pequenos(metricas_avaliacao.links())
    for linha in linhas:
        linha["url"] = request.build_absolute_uri(
            reverse("avaliacao-responder", kwargs={"token": linha["token"]})
        )
    contexto.update({"links": linhas, "form": NovoLinkDeAvaliacao()})
    return render(request, "painel/avaliacoes.html", contexto)


@require_POST
@staff_member_required
def gerar_link_avaliacao(request):
    form = NovoLinkDeAvaliacao(request.POST)
    if form.is_valid():
        link = form.save(commit=False)
        link.criado_por = request.user
        link.save()
        messages.success(request, f"Link criado para {link.curso.nome_curso} · {link.turma}.")
    else:
        messages.error(request, "Escolha um curso ativo e dê um nome à turma.")
    return redirect("painel-avaliacoes")


@require_POST
@staff_member_required
def fechar_link_avaliacao(request, pk):
    link = get_object_or_404(LinkDeAvaliacao, pk=pk)
    link.ativo = False
    link.save(update_fields=["ativo"])
    return redirect("painel-avaliacoes")


def _cursos_do_filtro(request, inicio):
    """(curso escolhido ou None, ids que podem entrar nas agregações de opinião)."""
    com_massa = metricas_avaliacao.cursos_com_massa(inicio, privacidade.K_MINIMO)
    curso_id = request.GET.get("curso")
    curso = Curso.objects.filter(pk=curso_id).first() if curso_id and curso_id.isdigit() else None
    if curso is None:
        return None, com_massa
    return curso, [curso.id] if curso.id in com_massa else []


@staff_member_required
def avaliacoes_resultados(request):
    inicio, contexto = _contexto_base(request, "avaliacoes")
    inicio = None
    contexto["sem_filtro_periodo"] = True
    curso, cursos = _cursos_do_filtro(request, inicio)

    resumo = metricas_avaliacao.resumo_por_curso(inicio)
    for linha in resumo:
        if linha["total"] < privacidade.K_MINIMO:
            linha.update(total=None, suprimido=True, nps=None, media=None)

    contexto.update({
        "curso": curso,
        "avaliacoes_com_massa": bool(cursos),
        "resumo": resumo,
        "cursos_avaliados": Curso.objects.filter(links_de_avaliacao__isnull=False).distinct().order_by("nome_curso"),
    })
    if cursos:
        blocos = metricas_avaliacao.por_pergunta(inicio, cursos)
        for bloco in blocos:
            if "distribuicao" in bloco:
                bloco["distribuicao"] = privacidade.suprimir_pequenos(bloco["distribuicao"])
                maior = max((d["total"] or 0 for d in bloco["distribuicao"]), default=0)
                for item in bloco["distribuicao"]:
                    item["largura"] = round((item["total"] or 0) / maior * 100) if maior else 0
        contexto["blocos"] = blocos
        contexto["fora_do_todos"] = len(resumo) - len(cursos) if curso is None else 0
    return render(request, "painel/avaliacoes_resultados.html", contexto)


@staff_member_required
def avaliacoes_csv(request):
    _contexto_base(request, "avaliacoes")
    inicio = None
    _, cursos = _cursos_do_filtro(request, inicio)
    if not cursos:
        if privacidade.K_MINIMO:
            messages.error(request, f"O CSV só sai para cursos com {privacidade.K_MINIMO} avaliações ou mais.")
        else:
            messages.error(request, "Nenhuma avaliação no histórico para exportar.")
        return redirect("painel-avaliacoes-resultados")

    resposta = HttpResponse(content_type="text/csv; charset=utf-8")
    resposta["Content-Disposition"] = 'attachment; filename="avaliacoes.csv"'
    resposta.write("\ufeff")  # BOM: o Excel abre os acentos certos
    escritor = csv.writer(resposta, delimiter=";")
    escritor.writerow(["curso", "pergunta", "resposta"])
    escritor.writerows(metricas_avaliacao.linhas_do_csv(inicio, cursos))
    return resposta