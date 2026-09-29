from django.shortcuts import get_object_or_404, render

from accounts.models import Interesse
from catalogo.models import Curso
from quiz.permissoes import tentativa_visivel


def curso_detalhe(request, pk):
    curso = get_object_or_404(
        Curso.objects.select_related("area_principal"), pk=pk, is_active=True
    )

    # De onde a pessoa veio: permite "voltar para o meu resultado", mostrar a
    # afinidade dela com este curso e salvar o interesse com o snapshot certo.
    tentativa_id = request.GET.get("tentativa", "")
    tentativa = tentativa_visivel(request, int(tentativa_id)) if tentativa_id.isdigit() else None

    afinidade = None
    if tentativa:
        rec = tentativa.recomendacoes.filter(curso=curso).first()
        afinidade = round(rec.score * 100) if rec else None

    salvo = (
        request.user.is_authenticated
        and Interesse.objects.filter(usuario=request.user, curso=curso)
        .exclude(status="removido").exists()
    )
    return render(request, "catalogo/curso_detalhe.html", {
        "curso": curso,
        "tentativa_id": tentativa.pk if tentativa else "",
        "afinidade": afinidade,
        "salvo": salvo,
    })