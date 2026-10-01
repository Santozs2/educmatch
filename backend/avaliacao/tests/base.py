from io import StringIO

from django.core.management import call_command
from django.urls import reverse

from avaliacao.models import LinkDeAvaliacao, Pergunta
from catalogo.models import Curso
from quiz.tests.base import BaseEducMatch


class BaseAvaliacao(BaseEducMatch):
    """Catálogo real + as perguntas do seed_avaliacao."""

    @classmethod
    def setUpTestData(cls):
        super().setUpTestData()
        call_command("seed_avaliacao", stdout=StringIO())

    def criar_link(self, curso=None, turma="2026/1 · Noite", **extra):
        return LinkDeAvaliacao.objects.create(curso=curso or Curso.objects.first(), turma=turma, **extra)

    def respostas_validas(self, nota=9, escala=4, escolha="Sim", texto=""):
        dados = {}
        for pergunta in Pergunta.objects.filter(ativa=True):
            chave = f"pergunta_{pergunta.id}"
            dados[chave] = {"nps": nota, "escala": escala, "escolha": escolha, "texto": texto}[pergunta.tipo]
        return dados

    def enviar(self, link, dados):
        return self.client.post(reverse("avaliacao-responder", args=[link.token]), dados)