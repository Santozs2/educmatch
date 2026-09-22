from django.urls import path
from django.views.generic import RedirectView

from quiz.web_views import acessar_questionario, pagina_quiz, resultado_pagina

urlpatterns = [
    path('', pagina_quiz, name='quiz-inicio'),
    path('questionario/<uuid:token>/', acessar_questionario, name='questionario-link'),
    path('resultado/<int:pk>/', resultado_pagina, name='quiz-resultado'),
    # O dashboard antigo virou o painel: o endereço velho só redireciona
    path('quiz/dashboard/', RedirectView.as_view(pattern_name='painel-dashboard', permanent=True), name='dashboard'),
]