from django.db import transaction
from rest_framework import generics, status
from rest_framework.response import Response
from rest_framework.views import APIView
from quiz.engine import Recomendacao
from quiz.models import Resposta, Questao, Tentativa_de_resposta
from quiz.serializers import RecomendacaoSerializer, Questao, EnvioSerializer, QuestaoSerializer
from functools import wraps

from django.conf import settings
from django.contrib.auth.views import redirect_to_login
from django.core.exceptions import PermissionDenied
from django.shortcuts import redirect, render
from django.urls import reverse
from .models import QuestionarioLink, Resposta

class QuestaoList(generics.ListAPIView):
    queryset = Questao.objects.all()
    serializer_class = Questao
    
class EnvioQuiz(APIView):
    def post(self, request):
        entrada = EnvioSerializer(data=request.data)
        entrada.is_valid(raise_exception=True)
        dados = entrada.validated_data
        
        with transaction.atomic():
            tentativa = Tentativa_de_resposta.objects.create(usuario=request.user)
            Resposta.objects.bulk_create(
                [
                    Resposta(tentativa=tentativa, questao=item["questao"], alternativa=item["alternativa"])
                    for item in dados["respostas"]
                ]
            )
            recomendacoes = Recomendacao(tentativa)
        return Response({"tentativa_id": tentativa.id, "recomendacoes" : RecomendacaoSerializer(recomendacoes, many=True). data}, status=status.HTTP_201_CREATED)
    
class ResultadoQuestao(generics.RetrieveAPIView):
    queryset = Questao.objects.all()
    serializer_class = QuestaoSerializer
    
    def recuerar(self, request, *args, **kwargs):
        tentativa = self.get_object.all()
        dados = RecomendacaoSerializer(tentativa, many=True).data
        return Response(dados, status=status.HTTP_200_OK)

def superuser_required(view):
    """Libera a view apenas para superusuarios ativos.

    Visitante anonimo vai para a tela de login; usuario logado sem permissao
    recebe 403 em vez de voltar para o login em looping.
    """

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
    cursos_com_interesse = cursos.filter(total_interesses__gt=0).count()

    contexto = {
        'total_respostas': total_respostas,
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
