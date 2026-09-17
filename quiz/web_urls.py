from django.urls import path
from quiz.web_views import acessar_questionario, pagina_quiz, resultado_pagina

urlpatterns = [
    path('', pagina_quiz, name='quiz-inicio'),
    path('questionario/<uuid:token>/', acessar_questionario, name='questionario-link'),
    path('resultado/<int:pk>/', resultado_pagina, name='quiz-resultado'),

    
]