from functools import wraps

from django.conf import settings
from django.contrib.auth.views import redirect_to_login
from django.core.exceptions import PermissionDenied
from django.http import JsonResponse
from django.shortcuts import redirect, render
from django.urls import reverse

from .models import QuestionarioLink, Resposta, Tentativa_de_resposta


def superuser_required(view):
    @wraps(view)
    def _wrapper(request, *args, **kwargs):
        usuario = request.user
        if not usuario.is_authenticated:
            return redirect_to_login(request.get_full_path(), reverse(settings.LOGIN_URL))
        if not (usuario.is_active and usuario.is_superuser):
            raise PermissionDenied("Apenas superusuarios podem acessar o dashboard.")
        return view(request, *args, **kwargs)

    return _wrapper


@superuser_required
def gerar_questionario_link(request):
    if request.method != "POST":
        return redirect("dashboard")

    link = QuestionarioLink.objects.create(criado_por=request.user)
    request.session["ultimo_questionario_link"] = str(link.token)
    questionario_url = request.build_absolute_uri(
        reverse("questionario-link", kwargs={"token": link.token})
    )

    if request.headers.get("x-requested-with") == "XMLHttpRequest":
        return JsonResponse({"success": True, "url": questionario_url})

    return redirect("dashboard")


@superuser_required
def dashboard_view(request):
    from django.db.models import Count, Q
    from catalogo.models import Curso
    from quiz.models import Questao

    cursos = Curso.objects.annotate(
        total_interesses=Count("interessados", distinct=True)
    ).order_by("-total_interesses", "nome_curso")
    perguntas = Questao.objects.filter(is_active=True).prefetch_related("alternativas")
    for pergunta in perguntas:
        alternativas = pergunta.alternativas.annotate(
            total_respostas=Count("respostas", filter=Q(respostas__tentativa__isnull=False))
        )
        pergunta.resultados = alternativas

    links = QuestionarioLink.objects.filter(ativo=True)
    ultimo_link = request.session.get("ultimo_questionario_link")
    ultimo_link_obj = links.filter(token=ultimo_link).first() if ultimo_link else links.first()
    total_respostas = Resposta.objects.count()
    total_quiz_completos = Tentativa_de_resposta.objects.filter(user__isnull=False).count()
    cursos_com_interesse = cursos.filter(total_interesses__gt=0).count()

    contexto = {
        'total_respostas': total_respostas,
        'total_quiz_completos': total_quiz_completos,
        'total_manifestacoes': cursos.aggregate(total=Count("interessados"))["total"] or 0,
        'cursos_com_interesse': cursos_com_interesse,
        'cursos': cursos,
        'perguntas': perguntas,
        'links': links[:5],
        'questionario_url': (
            request.build_absolute_uri(
                reverse("questionario-link", kwargs={"token": ultimo_link_obj.token})
            )
            if ultimo_link_obj else ""
        ),
    }
    
    return render(request, 'quiz/dashboard.html', contexto)
