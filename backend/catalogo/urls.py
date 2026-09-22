from django.urls import path
from catalogo.views import curso_detalhe

urlpatterns = [
    path("<int:pk>/", curso_detalhe, name="curso-detalhe"),
]