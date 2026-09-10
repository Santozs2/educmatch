from django.urls import path
from quiz.web_views import pagina_quiz, resultado_pagina

urlpatterns = [
    path('', pagina_quiz, name='quiz-inicio'),
    path('resultado/<int:pk>/', resultado_pagina, name='quiz-resultado'),

    
]