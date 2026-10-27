from django.urls import path
from painel import views

urlpatterns = [
    path("", views.dashboard, name="painel-dashboard"),
    path("quiz/", views.quiz_visao_geral, name="painel-quiz"),
    path("cursos/", views.cursos, name="painel-cursos"),
    path("cursos/<int:pk>/editar/", views.editar_curso, name="painel-editar-curso"),
    path("cursos/<int:pk>/remover/", views.remover_curso, name="painel-remover-curso"),
    path("areas/criar/", views.criar_area, name="painel-criar-area"),
    path("links/", views.links, name="painel-links"),
    path("interesse/", views.interesse, name="painel-interesse"),
    path("gerar-link/", views.gerar_link, name="painel-gerar-link"),
    path("fechar-link/", views.fechar_link, name="painel-fechar-link"),
    path("links/<int:pk>/fechar/", views.fechar_um_link, name="painel-fechar-um-link"),
    path("avaliacoes/", views.avaliacoes, name="painel-avaliacoes"),
    path("avaliacoes/gerar/", views.gerar_link_avaliacao, name="painel-avaliacoes-gerar"),
    path("avaliacoes/<int:pk>/fechar/", views.fechar_link_avaliacao, name="painel-avaliacoes-fechar"),
    path("avaliacoes/resultados/", views.avaliacoes_resultados, name="painel-avaliacoes-resultados"),
    path("avaliacoes/resultados.csv", views.avaliacoes_csv, name="painel-avaliacoes-csv"),
]