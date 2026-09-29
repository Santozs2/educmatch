from django.contrib.auth.views import LogoutView
from django.urls import path
from . import views

urlpatterns = [
    path("entrar/", views.EntrarView.as_view(), name="entrar"),
    path("cadastro_usuario/", views.cadastrar_conta, name="cadastro_usuario"),
    path("lista_interesse/", views.lista_interesse, name="lista_interesse"),
    path("lista_interesse/<int:pk>/remover/", views.remover_interesse, name="remover_interesse"),
    path("meus-testes/", views.minhas_tentativas, name="minhas-tentativas"),
    path("meu-perfil/", views.aluno_perfil, name="aluno-perfil"),
    path("interesse/salvar/", views.salvar_interesse, name="interesse-salvar"),
    path( "lista_interesse/<int:pk>/salvar/",views.salvar_interesse,name="salvar_interesse",),
    path("interesse/remover/", views.remover_interesse_por_curso, name="interesse-remover"),
    path("logout/", LogoutView.as_view(), name="logout"),
]