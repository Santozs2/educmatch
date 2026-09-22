from django.shortcuts import render, redirect, get_object_or_404
from django.urls import reverse
from urllib.parse import urlencode
from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_POST
from django.contrib.auth.views import LoginView
from django.contrib.auth import login as auth_login
from accounts.forms import LoginForm, CadastroForm
from accounts.models import Interesse
from catalogo.models import Curso
from quiz.models import Tentativa_de_resposta
from accounts.servicos import registrar_interesse

def _salvar_interesse_pendente(request):
    pendente = request.session.get("interesse_pendente")
    if not pendente or not request.user.is_authenticated:
        return None

    curso_id = pendente.get("curso_id")
    tentativa_id = pendente.get("tentativa_id")
    curso = Curso.objects.filter(pk=curso_id).first()
    if curso is None:
        request.session.pop("interesse_pendente", None)
        return None

    tentativa = None
    if tentativa_id:
        tentativa = Tentativa_de_resposta.objects.filter(pk=tentativa_id).first()

    registrar_interesse(request.user, curso, tentativa)
    request.session.pop("interesse_pendente", None)
    return tentativa_id


class EntrarView(LoginView):
    template_name = "accounts/entrar.html"
    authentication_form = LoginForm
    redirect_authenticated_user = True

    def get_success_url(self):
        sucesso_url = super().get_success_url()
        _salvar_interesse_pendente(self.request)
        return sucesso_url
    


def cadastrar_conta(request):
    if request.user.is_authenticated:
        return redirect('lista_interesse')
    
    if request.method == "POST":
        form = CadastroForm(request.POST)
        if form.is_valid():
            user = form.save()
            auth_login(request, user)
            _salvar_interesse_pendente(request)
            return redirect(request.POST.get("lista_interesse") or "quiz-inicio")
    else:
        form = CadastroForm()

    return render(request, "accounts/criar_conta.html", {"form": form})

@login_required
def lista_interesse(request):
    interesses = Interesse.objects.filter(usuario=request.user).select_related('curso')
    ultima_tentativa = Tentativa_de_resposta.objects.filter(
        user=request.user
    ).first()
    return render(
        request,
        "accounts/lista.html",
        {"interesses": interesses, "ultima_tentativa": ultima_tentativa},
    )

@require_POST
@login_required
def remover_interesse(request, pk):
    interesse = get_object_or_404(Interesse, pk=pk, usuario=request.user)
    interesse.delete()
    return redirect('lista_interesse')

@login_required
def interesse_remover(request, pk):
    item = get_object_or_404(Interesse, pk=pk, usuario=request.user)
    item.delete()
    return redirect("lista_interesse")


@require_POST
def salvar_interesse(request):
    curso_id = request.POST.get('curso_id')
    tentativa_id = request.POST.get('tentativa_id')
    curso = get_object_or_404(Curso, id=curso_id)
    
    if not request.user.is_authenticated:
        request.session['interesse_pendente'] = {
            "curso_id" : curso_id,
            "tentativa_id" : tentativa_id,
        }
        next_url = reverse("quiz-resultado", kwargs={"pk": tentativa_id}) if tentativa_id else reverse("quiz-inicio")
        login_url = f"{reverse('entrar')}?{urlencode({'next': next_url})}"
        return redirect(login_url)
    
    tentativa = None
    if tentativa_id:
        tentativa = Tentativa_de_resposta.objects.filter(pk=tentativa_id).first()

    item, criado = registrar_interesse(request.user, curso, tentativa)
    if not criado:
        item.delete()
        
    request.session.pop("interesse_pendente", None)
    if tentativa_id:
        return redirect("quiz-resultado", pk=tentativa_id)
    return redirect("lista_interesse")

@login_required
def minhas_tentativas(request):
    tentativas = Tentativa_de_resposta.objects.filter(user=request.user)
    return render(request, "accounts/tentativas.html", {"tentativas": tentativas})

@login_required
def aluno_perfil(request):
    tentativas = Tentativa_de_resposta.objects.filter(user=request.user).prefetch_related("recomendacoes__curso")
    interesses = Interesse.objects.filter(usuario=request.user).select_related("curso")
    historico = []
    for tentativa in tentativas:
        destaque = tentativa.recomendacoes.first()
        historico.append({
            "curso": destaque.curso if destaque else None,
            "match": round(destaque.score * 100) if destaque else 0,
            "data": tentativa.criado_em,
        })

    return render(request, "quiz/aluno_perfil.html", {
        "aluno": request.user,
        "curso_atual": interesses.first().curso if interesses.exists() else None,
        "progresso": {"percentual": 0},
        "estatisticas": {
            "aulas_concluidas": 0,
            "horas_estudadas": 0,
            "exercicios_feitos": 0,
            "sequencia_dias": 0,
        },
        "historico": historico,
    })