from django.urls import path
from painel.views import dashboard, gerar_link, fechar_link

urlpatterns = [
    path("", dashboard, name="painel-dashboard"),
    path("gerar-link/", gerar_link, name="painel-gerar-link"),
    path("fechar-link/", fechar_link, name="painel-fechar-link"),
]