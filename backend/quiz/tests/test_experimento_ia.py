import csv
import tempfile
from io import StringIO
from pathlib import Path

from django.core.management import call_command
from django.core.management.base import CommandError
from django.test import override_settings

from quiz.management.commands.experimento_ia import COLUNAS
from quiz.models import Tentativa_de_resposta
from quiz.tests.base import BaseEducMatch


@override_settings(LLM_ENABLED=True, LLM_PROVIDER="fake", LLM_PROMPT_VERSION="v1")
class ExperimentoIATest(BaseEducMatch):
    """Passo 11: o experimento grava o CSV e não deixa nada no banco."""

    def rodar(self, **opcoes):
        with tempfile.TemporaryDirectory() as pasta:
            saida = Path(pasta) / "experimento.csv"
            call_command("experimento_ia", pausa=0, saida=str(saida), stdout=StringIO(), **opcoes)
            with open(saida, encoding="utf-8-sig") as arquivo:
                return list(csv.DictReader(arquivo, delimiter=";"))

    def test_uma_linha_por_perfil_e_banco_intacto(self):
        linhas = self.rodar(n=3)

        self.assertEqual(len(linhas), 3)
        self.assertEqual(list(linhas[0]), COLUNAS)
        self.assertTrue(all(linha["texto_principal"] for linha in linhas))
        self.assertEqual(Tentativa_de_resposta.objects.count(), 0)

    def test_so_empates(self):
        linhas = self.rodar(n=2, so_empates=True)

        self.assertEqual(len(linhas), 2)
        self.assertTrue(all(int(linha["tamanho_tie_set"]) > 1 for linha in linhas))

    @override_settings(LLM_ENABLED=False)
    def test_recusa_com_a_llm_desligada(self):
        with self.assertRaises(CommandError):
            self.rodar(n=1)
