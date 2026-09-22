from io import StringIO

from django.contrib.auth import get_user_model
from django.core.management import call_command
from django.test import Client, TestCase

# CONFIRA OS NOMES antes de rodar: os models desta base sao importados dentro
# dos metodos, justamente para que um nome errado quebre um teste e nao a suite
# inteira. Os nomes reais estao no glossario (ver C1 a C6, secao 9).
SEEDS = ("seed_areas", "seed_cursos", "seed_questoes")


class BaseEducMatch(TestCase):
    """Base de todo teste que precisa do catalogo real.

    Os seeds rodam UMA vez por classe; cada teste roda em transacao com rollback.
    """

    @classmethod
    def setUpTestData(cls):
        silencio = StringIO()
        for comando in SEEDS:
            call_command(comando, stdout=silencio)

    def setUp(self):
        # DisallowedHost: 'testserver' -- ver Bugs e licoes, Ambiente (Windows)
        self.client = Client(SERVER_NAME="localhost")

    def criar_usuario(self, email="aluno@exemplo.com", **extra):
        return get_user_model().objects.create_user(
            email=email, password="afinidade-2026", **extra
        )

    def payload_do_quiz(self, nome="Visitante", coluna=0):
        """O POST do formulario do quiz, escolhendo sempre a alternativa `coluna`."""
        from quiz.models import Questao

        dados = {"respondido_por": nome}
        for questao in Questao.objects.filter(is_active=True).order_by("id"):
            alternativas = list(questao.alternativas.order_by("id"))
            dados[f"questao_{questao.id}"] = alternativas[coluna % len(alternativas)].id
        return dados

    def responder_tudo(self, nome="Visitante", coluna=0):
        """Responde o quiz inteiro pelo formulario. Devolve a resposta HTTP."""
        return self.client.post("/", self.payload_do_quiz(nome, coluna))

    def criar_tentativa(self, dono=None, coluna=0):
        """Uma tentativa ja calculada pela engine, com ou sem dono."""
        from quiz.engine import recomedacao
        from quiz.models import Questao, Resposta, Tentativa_de_resposta

        tentativa = Tentativa_de_resposta.objects.create(user=dono, respondido_por="Teste")
        for questao in Questao.objects.filter(is_active=True).order_by("id"):
            alternativas = list(questao.alternativas.order_by("id"))
            Resposta.objects.create(
                tentativa=tentativa, questao=questao,
                alternativa=alternativas[coluna % len(alternativas)],
            )
        recomedacao(tentativa)
        return tentativa

    def dados_de_cadastro(self, email="ana@exemplo.com"):
        return {
            "first_name": "Ana",
            "email": email,
            "password1": "afinidade-2026",
            "password2": "afinidade-2026",
        }