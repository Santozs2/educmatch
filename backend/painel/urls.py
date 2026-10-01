from django.urls import path
from painel import views

urlpatterns = [
    path("", views.dashboard, name="painel-dashboard"),
    path("quiz/", views.quiz_visao_geral, name="painel-quiz"),
    path("cursos/", views.cursos, name="painel-cursos"),
    path("links/", views.links, name="painel-links"),
    path("interesse/", views.interesse, name="painel-interesse"),
    path("gerar-link/", views.gerar_link, name="painel-gerar-link"),
    path("fechar-link/", views.fechar_link, name="painel-fechar-link"),
    path("links/<int:pk>/fechar/", views.fechar_um_link, name="painel-fechar-um-link"),
]
