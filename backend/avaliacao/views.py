from django.db import transaction
from django.shortcuts import redirect, render

from .forms import FormularioDeAvaliacao
from .models import ItemDeResposta, LinkDeAvaliacao, Pergunta, RespostaDeAvaliacao

# Os links que este navegador já respondeu. É uma trava leve: impede o envio
# repetido sem querer (duplo clique, voltar e reenviar), mas não é um controle
# forte. Um controle forte exigiria saber quem respondeu, e aí não seria anônimo.
CHAVE_SESSAO = "avaliacoes_respondidas"


def _link_ativo(token):
    return LinkDeAvaliacao.objects.select_related("curso").filter(token=token, ativo=True).first()


def responder(request, token):
    link = _link_ativo(token)
    if link is None:
        return render(request, "avaliacao/link_invalido.html", status=404)
    if link.pk in request.session.get(CHAVE_SESSAO, []):
        return redirect("avaliacao-obrigado", token=token)

    perguntas = Pergunta.objects.filter(ativa=True)
    form = FormularioDeAvaliacao(perguntas, request.POST or None)
    if request.method == "POST" and form.is_valid():
        with transaction.atomic():
            resposta = RespostaDeAvaliacao.objects.create(link=link)
            itens = []
            for pergunta in form.perguntas:
                valor = form.cleaned_data.get(f"pergunta_{pergunta.id}")
                if valor in (None, ""):
                    continue  # pergunta opcional deixada em branco
                if pergunta.tipo in ("nps", "escala"):
                    itens.append(ItemDeResposta(resposta=resposta, pergunta=pergunta, numero=valor))
                else:
                    itens.append(ItemDeResposta(resposta=resposta, pergunta=pergunta, texto=valor.strip()))
            ItemDeResposta.objects.bulk_create(itens)

        respondidas = request.session.get(CHAVE_SESSAO, [])
        request.session[CHAVE_SESSAO] = respondidas + [link.pk]
        return redirect("avaliacao-obrigado", token=token)

    return render(request, "avaliacao/responder.html", {"link": link, "form": form})


def obrigado(request, token):
    link = LinkDeAvaliacao.objects.select_related("curso").filter(token=token).first()
    return render(request, "avaliacao/obrigado.html", {"link": link})