from quiz.models import Tentativa_de_resposta

def tentativa_visivel(request, pk):
    tentativa = Tentativa_de_resposta.objects.filter(pk=pk).first()
    if tentativa is None:
        return None
    if tentativa.user_id is not None:
        return tentativa if tentativa.user_id == request.user.id else None
    return tentativa if tentativa.pk in request.session.get("minhas_tentativas", []) else None