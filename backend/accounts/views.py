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
from accounts.servicos import registrar_interesse, remover_da_lista
from quiz.permissoes import tentativa_visivel

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

    tentativa = tentativa_visivel(request, int(tentativa_id)) if str(tentativa_id).isdigit() else None

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
    interesses = (Interesse.objects.filter(usuario=request.user).exclude(status="removido").select_related("curso"))
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
    remover_da_lista(interesse)
    return redirect('lista_interesse')

@login_required
def interesse_remover(request, pk):
    item = get_object_or_404(Interesse, pk=pk, usuario=request.user)
    item.delete()
    return redirect("lista_interesse")


@require_POST
def salvar_interesse(request):
    curso_id = request.POST.get('curso_id')
    tentativa_id = request.POST.get('tentativa_id', '')
    curso = get_object_or_404(Curso, id=curso_id)

    if not request.user.is_authenticated:
        request.session['interesse_pendente'] = {
            "curso_id": curso_id,
            "tentativa_id": tentativa_id,
        }
        next_url = reverse("quiz-resultado", kwargs={"pk": tentativa_id}) if tentativa_id else reverse("quiz-inicio")
        login_url = f"{reverse('entrar')}?{urlencode({'next': next_url})}"
        return redirect(login_url)

    tentativa = tentativa_visivel(request, int(tentativa_id)) if tentativa_id.isdigit() else None
    registrar_interesse(request.user, curso, tentativa)

    request.session.pop("interesse_pendente", None)
    if tentativa_id:
        return redirect("quiz-resultado", pk=tentativa_id)
    return redirect("lista_interesse")

@require_POST
@login_required
def remover_interesse_por_curso(request):
    interesse = get_object_or_404(
        Interesse, usuario=request.user, curso_id=request.POST.get("curso_id")
    )
    remover_da_lista(interesse)
    destino = reverse("curso-detalhe", args=[interesse.curso_id])
    tentativa_id = request.POST.get("tentativa_id", "")
    if tentativa_id.isdigit():
        destino += f"?tentativa={tentativa_id}"
    return redirect(destino)

@login_required
def minhas_tentativas(request):
    tentativas = Tentativa_de_resposta.objects.filter(user=request.user).prefetch_related(
        "recomendacoes__curso"
    )
    return render(request, "accounts/tentativas.html", {"tentativas": tentativas})

@login_required
def aluno_perfil(request):
    tentativas = Tentativa_de_resposta.objects.filter(user=request.user).prefetch_related(
        "recomendacoes__curso"
    )
    historico = []
    for tentativa in tentativas:
        destaque = next(iter(tentativa.recomendacoes.all()), None)
        historico.append({
            "tentativa_id": tentativa.pk,
            "curso": destaque.curso if destaque else None,
            "match": round(destaque.score * 100) if destaque else None,
            "data": tentativa.criado_em,
        })
    interesses = (
        Interesse.objects.filter(usuario=request.user)
        .exclude(status="removido")
        .select_related("curso", "curso__area_principal")
    )
    return render(request, "quiz/aluno_perfil.html", {
        "total_de_testes": len(historico),
        "total_na_lista": interesses.count(),
        "interesses": interesses,
        "historico": historico,
    })