from django.urls import path
from quiz.views import dashboard_view, gerar_questionario_link
from quiz.web_views import acessar_questionario, pagina_quiz, resultado_pagina

urlpatterns = [
    path('', pagina_quiz, name='quiz-inicio'),
    path('questionario/<uuid:token>/', acessar_questionario, name='questionario-link'),
    path('resultado/<int:pk>/', resultado_pagina, name='quiz-resultado'),
    # Continuam em /quiz/dashboard/ para nenhum link ou favorito quebrar
    path('quiz/dashboard/', dashboard_view, name='dashboard'),
    path('quiz/dashboard/gerar-link/', gerar_questionario_link, name='gerar-questionario-link'),
]
