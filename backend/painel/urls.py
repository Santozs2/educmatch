from django.urls import path
from painel.views import dashboard, fechar_link, gerar_link, quiz_visao_geral

urlpatterns = [
    path("", dashboard, name="painel-dashboard"),
    path("quiz/", quiz_visao_geral, name="painel-quiz"),
    path("gerar-link/", gerar_link, name="painel-gerar-link"),
    path("fechar-link/", fechar_link, name="painel-fechar-link"),
]
