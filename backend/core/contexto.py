from django.conf import settings


def escola(request):
    """Os dados da escola em todo template: {{ escola.nome }}, {{ escola.telefone }}..."""
    return {"escola": settings.ESCOLA}


def versao(request):
    """O commit que está no ar, para o <meta name="versao"> do base.html."""
    return {"versao": settings.VERSAO}
