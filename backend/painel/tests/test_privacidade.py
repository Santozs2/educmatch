from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse

from painel.privacidade import K_MINIMO, suprimir_pequenos


class SupressaoTest(TestCase):
    def test_celula_pequena_e_suprimida_mas_a_linha_fica(self):
        linhas = [{"nome": "A", "total": 9}, {"nome": "B", "total": 2}]

        saida = suprimir_pequenos(linhas)

        self.assertEqual(len(saida), 2, "esconder a linha vazaria pela omissao")
        self.assertEqual(saida[0]["total"], 9)
        self.assertIsNone(saida[1]["total"])
        self.assertTrue(saida[1]["suprimido"])

    def test_a_funcao_nao_altera_a_entrada(self):
        linhas = [{"nome": "B", "total": 2}]
        suprimir_pequenos(linhas)
        self.assertEqual(linhas[0]["total"], 2)


class AcessoAoPainelTest(TestCase):
    def setUp(self):
        Usuario = get_user_model()
        self.comum = Usuario.objects.create_user(email="aluno@exemplo.com", password="x-2026-y")
        self.staff = Usuario.objects.create_user(
            email="coord@exemplo.com", password="x-2026-y", is_staff=True
        )

    def test_anonimo_nao_entra(self):
        resposta = self.client.get(reverse("painel-dashboard"))
        self.assertEqual(resposta.status_code, 302)

    def test_usuario_comum_nao_entra(self):
        self.client.force_login(self.comum)
        resposta = self.client.get(reverse("painel-dashboard"))
        self.assertNotEqual(resposta.status_code, 200)

    def test_staff_entra(self):
        self.client.force_login(self.staff)
        resposta = self.client.get(reverse("painel-dashboard"))
        self.assertEqual(resposta.status_code, 200)

    def test_nenhum_nome_de_respondente_aparece_na_pagina(self):
        """A regra de privacidade, verificada no HTML servido."""
        self.criar_tentativas(nomes=["Ana Zoraide", "Bento Kling", "Cleo Vasquez"])
        self.client.force_login(self.staff)

        corpo = self.client.get(reverse("painel-dashboard")).content.decode()

        for nome in ("Ana Zoraide", "Bento Kling", "Cleo Vasquez"):
            self.assertNotIn(nome, corpo)