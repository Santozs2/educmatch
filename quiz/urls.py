from django.urls import path
from . import views

urlpatterns = [
    path("questoes/", views.QuestaoList.as_view(), name="questao-list"),
    path("envio/", views.EnvioQuiz.as_view(), name="envio-list"),
    path("resultados/", views.ResultadoQuestao.as_view(), name="resultado-list"),
    path('dashboard/', views.dashboard_view, name='dashboard'),
    path('dashboard/gerar-link/', views.gerar_questionario_link, name='gerar-questionario-link'),
]