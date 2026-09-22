from django.contrib.auth.signals import user_logged_in
from django.dispatch import receiver

from quiz.models import Tentativa_de_resposta


@receiver(user_logged_in)
def adotar_tentativas_da_sessao(sender, request, user, **kwargs):
    """C6 -- passo 3: a tentativa anonima ganha dono ao entrar.

    Duas condicoes, as duas obrigatorias:
      1. o id esta na sessao DESTE navegador  -> nao adota tentativa alheia
      2. a tentativa ainda nao tem dono       -> nao readota a ja adotada
    """
    ids = request.session.get("minhas_tentativas", [])
    if not ids:
        return

    Tentativa_de_resposta.objects.filter(
        id__in=ids,
        user__isnull=True,
    ).update(user=user)