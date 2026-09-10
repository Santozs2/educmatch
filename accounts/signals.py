from django.contrib.auth.signals import user_logged_in
from django.dispatch import receiver
from quiz.models import Questao

@receiver(user_logged_in)
def tentativas_de_sessao(sender, request, user, **kwargs):
    ids = request.session.get('minhas_tentativas', [])
    if not ids:
        return
    
    questoes = Questao.objects.filter(id__in=ids)