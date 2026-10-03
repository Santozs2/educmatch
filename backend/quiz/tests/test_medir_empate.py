from io import StringIO

from django.core.management import call_command

from quiz.management.commands.medir_empate import fracao_abaixo
from quiz.tests.base import BaseEducMatch


class MedirEmpateTest(BaseEducMatch):
    """CAL-01: o comando que sustenta a escolha do EMPATE roda e é reprodutível."""

    def medir(self, **opcoes):
        saida = StringIO()
        call_command("medir_empate", stdout=saida, **opcoes)
        return saida.getvalue()

    def test_mostra_a_tabela_e_a_regua_atual(self):
        saida = self.medir(n=50)

        self.assertIn("Perfis sorteados: 50", saida)
        self.assertIn("Régua atual: EMPATE = 0.02", saida)
        self.assertIn("sorteados: baixa (empate)", saida)

    def test_mesma_semente_mesmo_resultado(self):
        self.assertEqual(self.medir(n=50, semente=7), self.medir(n=50, semente=7))

    def test_fracao_abaixo(self):
        self.assertEqual(fracao_abaixo([0.01, 0.03, 0.05, 0.07], 0.04), 0.5)
        self.assertIsNone(fracao_abaixo([], 0.04))