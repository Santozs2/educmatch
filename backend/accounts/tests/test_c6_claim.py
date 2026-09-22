from django.urls import reverse

from quiz.models import Tentativa_de_resposta
from quiz.tests.base import BaseEducMatch


class C6ClaimTest(BaseEducMatch):
    """C6 -- claim da tentativa anonima."""

    def test_tentativa_anonima_ganha_dono_ao_criar_conta(self):
        """O caminho completo: responde anonimo, cria conta, ve no historico."""
        self.responder_tudo(nome="Visitante")
        tentativa = Tentativa_de_resposta.objects.latest("id")
        self.assertIsNone(tentativa.user)

        self.client.post(reverse("cadastro_usuario"), self.dados_de_cadastro())

        tentativa.refresh_from_db()
        self.assertIsNotNone(tentativa.user)
        self.assertEqual(tentativa.user.email, "ana@exemplo.com")

    def test_historico_mostra_a_tentativa_adotada(self):
        """A consequencia verificavel que hoje devolve vazio."""
        self.responder_tudo()
        self.client.post(reverse("cadastro_usuario"), self.dados_de_cadastro())

        resposta = self.client.get(reverse("minhas-tentativas"))

        self.assertEqual(len(resposta.context["tentativas"]), 1)

    def test_nao_adota_tentativa_que_nao_esta_na_minha_sessao(self):
        """Condicao 1: sem ela, ids na mao adotariam tentativa alheia."""
        outro_navegador = self.client_class(SERVER_NAME="localhost")
        outro_navegador.post("/", self.payload_do_quiz())
        alheia = Tentativa_de_resposta.objects.latest("id")

        self.client.post(reverse("cadastro_usuario"), self.dados_de_cadastro())

        alheia.refresh_from_db()
        self.assertIsNone(alheia.user)

    def test_nao_readota_tentativa_que_ja_tem_dono(self):
        """Condicao 2: uma vez adotada, nao troca de dono."""
        primeiro = self.criar_usuario("primeiro@exemplo.com")
        tentativa = self.criar_tentativa(dono=primeiro)
        sessao = self.client.session
        sessao["minhas_tentativas"] = [tentativa.pk]
        sessao.save()

        self.client.post(reverse("cadastro_usuario"), self.dados_de_cadastro())

        tentativa.refresh_from_db()
        self.assertEqual(tentativa.user, primeiro)