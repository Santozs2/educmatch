from django.shortcuts import get_object_or_404, redirect, render

from accounts.models import Interesse
from catalogo.models import Curso
from quiz.permissoes import tentativa_visivel


def curso_detalhe(request, pk):
    curso = get_object_or_404(
        Curso.objects.select_related("area_principal"), pk=pk, is_active=True
    )

    # O detalhe só existe a partir de um resultado: é ele que dá a afinidade,
    # o "voltar para o meu resultado" e o snapshot certo ao salvar o interesse.
    tentativa_id = request.GET.get("tentativa", "")
    tentativa = tentativa_visivel(request, int(tentativa_id)) if tentativa_id.isdigit() else None
    if tentativa is None:
        return redirect("quiz-inicio")

    rec = tentativa.recomendacoes.filter(curso=curso).first()
    if rec is None:
        # Curso que não está neste resultado: volta para o resultado.
        return redirect("quiz-resultado", pk=tentativa.pk)

    salvo = (
        request.user.is_authenticated
        and Interesse.objects.filter(usuario=request.user, curso=curso)
        .exclude(status="removido").exists()
    )
    return render(request, "catalogo/curso_detalhe.html", {
        "curso": curso,
        "tentativa_id": tentativa.pk,
        "afinidade": round(rec.score * 100),
        "salvo": salvo,
    })
