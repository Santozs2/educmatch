from django.conf import settings

def escola(request):
    return {"escola": settings.ESCOLA}