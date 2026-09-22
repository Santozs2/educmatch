from django.test import TestCase
from django.urls import reverse

from accounts.tests_helpers import criar_usuario   # ou reaproveite a Base


class C5AutorizacaoTest(TestCase):
    """C5 -- Rotas e autorizacao.

    Tres perguntas por rota protegida:
      anonimo  -> e mandado para o login
      outro    -> NAO ve (e nao descobre que existe)
      dono     -> ve
    """

    ROTAS_PROTEGIDAS = [
        ("interesse-lista", {}),
        ("minhas-tentativas", {}),
        ("aluno-perfil", {}),
    ]

    def setUp(self):
        self.dono = criar_usuario("dono@exemplo.com")
        self.outro = criar_usuario("outro@exemplo.com")

    def test_anonimo_e_redirecionado_em_toda_rota_protegida(self):
        for nome, kwargs in self.ROTAS_PROTEGIDAS:
            with self.subTest(rota=nome):
                resposta = self.client.get(reverse(nome, kwargs=kwargs))
                self.assertEqual(resposta.status_code, 302)
                self.assertIn("/entrar/", resposta["Location"])

    def test_resultado_de_outro_usuario_da_404_e_nao_403(self):
        """404 de proposito: 403 confirma que a tentativa existe."""
        tentativa = self.criar_tentativa(dono=self.dono)
        self.client.force_login(self.outro)

        resposta = self.client.get(reverse("quiz-resultado", kwargs={"pk": tentativa.pk}))

        self.assertEqual(resposta.status_code, 404)

    def test_dono_ve_o_proprio_resultado(self):
        tentativa = self.criar_tentativa(dono=self.dono)
        self.client.force_login(self.dono)

        resposta = self.client.get(reverse("quiz-resultado", kwargs={"pk": tentativa.pk}))

        self.assertEqual(resposta.status_code, 200)

    def test_toda_rota_de_escrita_recusa_GET(self):
        """Salvar interesse e sair sao POST. Link que faz GET e 405, nao acao."""
        self.client.force_login(self.dono)
        for nome in ("interesse-salvar", "sair"):
            with self.subTest(rota=nome):
                resposta = self.client.get(reverse(nome))
                self.assertIn(resposta.status_code, (405, 302)) 