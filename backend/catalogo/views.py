from django.shortcuts import render, get_object_or_404
from accounts.models import Interesse
from catalogo.models import Curso

def curso_detalhe(request, pk):
    curso = get_object_or_404(
        Curso.objects.select_related("area_principal"), pk=pk, is_active=True
    )
    tentativa_id = request.GET.get("tentativa", "")
    if not tentativa_id.isdigit():
        tentativa_id = ""

    salvo = (
        request.user.is_authenticated
        and Interesse.objects.filter(usuario=request.user, curso=curso).exists()
    )
    return render(request, "catalogo/curso_detalhe.html", {
        "curso": curso,
        "tentativa_id": tentativa_id,
        "salvo": salvo,
    })
