from quiz.models import Tentativa_de_resposta


def tentativa_visivel(request, pk):
    """A tentativa `pk`, se esta pessoa pode vê-la; senão None.

    Mesma regra do resultado (contrato C6): tentativa com dono só para o dono;
    tentativa anônima só no navegador que a respondeu (está na sessão).
    """
    tentativa = Tentativa_de_resposta.objects.filter(pk=pk).first()
    if tentativa is None:
        return None
    if tentativa.user_id is not None:
        return tentativa if tentativa.user_id == request.user.id else None
    return tentativa if tentativa.pk in request.session.get("minhas_tentativas", []) else None