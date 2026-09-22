from django.conf import settings


def escola(request):
    """Os dados da escola em todo template: {{ escola.nome }}, {{ escola.telefone }}..."""
    return {"escola": settings.ESCOLA}