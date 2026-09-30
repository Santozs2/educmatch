from django.test import Client

from accounts.models import Interesse
from catalogo.models import Area, Curso
from quiz.models import Recomendacao, Tentativa_de_resposta
from quiz.tests.base import BaseEducMatch


class BasePainel(BaseEducMatch):
    """Base dos testes do painel: catálogo real (seeds) e fábricas de dados."""

    def criar_staff(self, email="coord@exemplo.com"):
        return self.criar_usuario(email, is_staff=True)

    def responder_anonimo(self, nome="Visitante", coluna=0):
        """Responde o quiz num navegador novo: cada chamada é uma tentativa anônima."""
        from quiz.models import Questao

        navegador = Client(SERVER_NAME="localhost")
        dados = {"respondido_por": nome}
        for questao in Questao.objects.filter(is_active=True).order_by("id"):
            alternativas = list(questao.alternativas.order_by("id"))
            dados[f"questao_{questao.id}"] = alternativas[coluna % len(alternativas)].id
        navegador.post("/", dados)
        return Tentativa_de_resposta.objects.latest("id")

    def criar_tentativas(self, quantidade=None, nomes=None):
        nomes = nomes or [f"Visitante {i}" for i in range(quantidade)]
        return [self.responder_anonimo(nome, coluna=i) for i, nome in enumerate(nomes)]

    def criar_curso(self, **extra):
        dados = {
            "nome_curso": "Curso de teste",
            "descricao": "Criado pelo teste",
            "area_principal": Area.objects.first(),
            "duracao": 100,
        }
        dados.update(extra)
        return Curso.objects.create(**dados)

    def criar_curso_com(self, recomendacoes=0, interesses=0):
        """Um curso com N recomendações (em tentativas diferentes) e M interessados."""
        curso = self.criar_curso()
        for _ in range(recomendacoes):
            tentativa = Tentativa_de_resposta.objects.create()
            Recomendacao.objects.create(tentativa=tentativa, curso=curso, score=0.5, rank_engine=2, rank_final=2)
        for i in range(interesses):
            usuario = self.criar_usuario(f"interessado{i}@exemplo.com")
            Interesse.objects.create(usuario=usuario, curso=curso)
        return curso

    def criar_tentativa_com_explicacao(self, explicacao):
        tentativa = Tentativa_de_resposta.objects.create()
        Recomendacao.objects.create(
            tentativa=tentativa, curso=Curso.objects.first(), score=0.9, rank_engine=1, rank_final=1, explicacao=explicacao
        )
        return tentativa