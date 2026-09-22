from django.db import transaction 
from django.http import Http404 
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from urllib.parse import urlencode
from quiz.models import Questao, QuestionarioLink, Resposta, Tentativa_de_resposta
from catalogo.models import Curso
from accounts.models import Interesse
from quiz.engine import recomedacao

def perguntas_ativas():
    return Questao.objects.filter(is_active=True).prefetch_related("alternativas")

def areas_da_recomendacao(recomendacao):
    explicacao = recomendacao.explicacao  # JSONField: já chega como dict
    if not isinstance(explicacao, dict):
        return []

    areas = explicacao.get("top_areas", [])
    if not isinstance(areas, list):
        return []

    areas_norm = []
    for area in areas:
        if not isinstance(area, dict):
            continue
        area_norm = dict(area)
        area_norm["area_name"] = area_norm.get("area_name") or area_norm.get("area_nome") or area_norm.get("area")
        areas_norm.append(area_norm)
    return areas_norm

def pagina_quiz(request):
    questoes = perguntas_ativas()
    
    if request.method != "POST":
        respondido_por = request.GET.get("respondido_por", "").strip()[:100]
        etapa = request.GET.get("etapa")
        if respondido_por and not etapa:
            request.session.pop("quiz_respostas", None)
            request.session.pop("quiz_respondido_por", None)

        respostas_salvas = request.session.get("quiz_respostas", {})
        for questao in questoes:
            marcada = respostas_salvas.get(str(questao.id))
            questao.marcada_id = int(marcada) if marcada else None
        return render(
            request,
            "quiz/quiz.html",
            {
                "questoes": questoes,
                "respondido_por": respondido_por or request.session.get("quiz_respondido_por", ""),
                "quiz_iniciado": bool(respondido_por or etapa),
            },
        )
    
    respondido_por = request.POST.get("respondido_por", "").strip()[:100]
    
    if not respondido_por and request.user.is_authenticated:
        respondido_por = request.user.first_name
    respostas_salvas = request.session.get("quiz_respostas", {})
    selecionadas = {}
    for questao in questoes:
        enviado = request.POST.get(f"questao_{questao.id}") or respostas_salvas.get(str(questao.id))
        escolha = next(
            (c for c in questao.alternativas.all() if str(c.id) == enviado), None
        )
        if escolha:
            selecionadas[questao] = escolha
    if len(selecionadas) < len(questoes):
        request.session["quiz_respostas"] = {
            str(questao.id): escolha.id
            for questao, escolha in selecionadas.items()
        }
        request.session["quiz_respondido_por"] = respondido_por
        request.session.modified = True
        proxima = next(
            (indice + 1 for indice, questao in enumerate(questoes) if questao not in selecionadas),
            1,
        )
        query = urlencode({"respondido_por": respondido_por, "etapa": proxima})
        return redirect(f"{reverse('quiz-inicio')}?{query}#questao-{proxima}")
    
    usuario = request.user if request.user.is_authenticated else None
    questionario_link = QuestionarioLink.objects.filter(
        token=request.session.get("questionario_link_token"), ativo=True
    ).first()
    with transaction.atomic():
        tentativa = Tentativa_de_resposta.objects.create(
            respondido_por=respondido_por,
            user=usuario,
            questionario_link=questionario_link,
        )
        Resposta.objects.bulk_create(
            [
                Resposta(tentativa=tentativa, questao=questao, alternativa=escolha)
                for questao, escolha in selecionadas.items()
            ]
        )
        recomedacao(tentativa)
    tentativas = request.session.setdefault("minhas_tentativas", [])
    tentativas.append(tentativa.pk)
    request.session.pop("quiz_respostas", None)
    request.session.pop("quiz_respondido_por", None)
    request.session.modified = True
    
    return redirect("quiz-resultado", pk=tentativa.pk)


def acessar_questionario(request, token):
    link = get_object_or_404(QuestionarioLink, token=token, ativo=True)
    request.session["questionario_link_token"] = str(link.token)
    request.session.pop("quiz_respostas", None)
    request.session.pop("quiz_respondido_por", None)
    return redirect("quiz-inicio")

def resultado_pagina(request,pk):
    tentativa = get_object_or_404(Tentativa_de_resposta, pk=pk)
    e_dono = tentativa.user_id is not None and tentativa.user_id == getattr(request.user, "id", None)
    esta_na_sessao = tentativa.pk in request.session.get("minhas_tentativas", [])
    if tentativa.user_id is not None and not e_dono:
        raise Http404
    if tentativa.user_id is None and not esta_na_sessao:
        raise Http404
    
    recomedacoes = tentativa.recomendacoes.select_related("curso__area_principal")
    itens = [
        {
            "rank": rec.rank,
            "match": round(rec.score * 100),
            "curso": rec.curso,
            "areas": areas_da_recomendacao(rec),
            
        }
        for rec in recomedacoes
    ]
    pendente = request.session.get("interesse_pendente")
    curso_pendente = None
    if pendente and str(pendente.get("tentativa_id")) == str(pk):
        curso_pendente = Curso.objects.filter(pk=pendente.get("curso_id")).first()
    interesses_salvos = set()
    if request.user.is_authenticated:
        interesses_salvos = set(Interesse.objects.filter(usuario=request.user).values_list("curso_id", flat=True))
    return render(request, "quiz/resultado.html", 
            {
                "tentativa" : tentativa,
                "destaque" : itens[0] if itens else None,
                "outros" : itens[1:],
                "curso_pendente" : curso_pendente,
                "interesses_salvos" : interesses_salvos,
            }
    )