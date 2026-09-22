from django.http import Http404
from django.shortcuts import get_object_or_404, render

from accounts.models import Interesse
from catalogo.models import Curso
from quiz.models import Tentativa_de_resposta


def tentativa_visivel(request, pk):
    tentativa = Tentativa_de_resposta.objects.filter(pk=pk).first()
    if tentativa is None:
        return None
    if tentativa.user_id is not None:
        return tentativa if tentativa.user_id == request.user.id else None
    return tentativa if tentativa.pk in request.session.get("minhas_tentativas", []) else None


def curso_detalhe(request, pk):
    curso = get_object_or_404(Curso.objects.select_related("area_principal"), pk=pk, is_active=True)

    tentativa_id = request.GET.get("tentativa")
    tentativa = None
    if tentativa_id:
        tentativa = Tentativa_de_resposta.objects.filter(pk=tentativa_id).first()
        if tentativa is not None:
            e_dono = tentativa.user_id is not None and tentativa.user_id == getattr(request.user, "id", None)
            esta_na_sessao = tentativa.pk in request.session.get("minhas_tentativas", [])

            if tentativa.user_id is not None and not e_dono:
                tentativa = None
            elif tentativa.user_id is None and not esta_na_sessao:
                tentativa = None

    afinidade = None
    if tentativa is not None:
        recomendacao = tentativa.recomendacoes.filter(curso=curso).first()
        if recomendacao is not None:
            afinidade = round(recomendacao.score * 100)
            

    salvo = False
    if request.user.is_authenticated:
        salvo = Interesse.objects.filter(usuario=request.user, curso=curso).exists()

    return render(
        request,
        "catalogo/curso_detalhe.html",
        {
            "curso": curso,
            "tentativa_id": tentativa_id,
            "afinidade": afinidade,
            "salvo": salvo,
        },
    )