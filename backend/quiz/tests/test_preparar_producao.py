import tempfile
from io import StringIO
from pathlib import Path
from unittest import mock

from django.core.management import call_command
from django.test import SimpleTestCase, override_settings

from quiz.management.commands.preparar_producao import ETAPAS

CHAMAR = "quiz.management.commands.preparar_producao.call_command"


class PrepararProducaoTest(SimpleTestCase):
    """U3: o boot só prepara o banco quando a versão no ar muda."""

    def setUp(self):
        pasta = tempfile.TemporaryDirectory()
        self.addCleanup(pasta.cleanup)
        self.marcador = Path(pasta.name) / "data" / ".versao-preparada"

    def preparar(self, versao, **opcoes):
        with override_settings(VERSAO=versao, MARCADOR_PREPARO=str(self.marcador)), \
                mock.patch(CHAMAR) as chamar:
            call_command("preparar_producao", stdout=StringIO(), **opcoes)
        return [chamada.args[0] for chamada in chamar.call_args_list]

    def test_primeiro_boot_prepara_tudo_e_grava_o_marcador(self):
        self.assertEqual(self.preparar("abc1234"), [nome for nome, _ in ETAPAS])
        self.assertEqual(self.marcador.read_text(encoding="utf-8"), "abc1234")

    def test_boot_da_mesma_versao_nao_faz_nada(self):
        self.preparar("abc1234")
        self.assertEqual(self.preparar("abc1234"), [])

    def test_versao_nova_prepara_de_novo(self):
        self.preparar("abc1234")
        self.assertEqual(self.preparar("def5678"), [nome for nome, _ in ETAPAS])
        self.assertEqual(self.marcador.read_text(encoding="utf-8"), "def5678")

    def test_sem_versao_sempre_prepara(self):
        self.preparar("dev")
        self.assertEqual(self.preparar("dev"), [nome for nome, _ in ETAPAS])

    def test_forcar_prepara_mesmo_sem_mudanca(self):
        self.preparar("abc1234")
        self.assertEqual(self.preparar("abc1234", forcar=True), [nome for nome, _ in ETAPAS])

    def test_etapa_que_falha_nao_grava_o_marcador(self):
        with override_settings(VERSAO="abc1234", MARCADOR_PREPARO=str(self.marcador)), \
                mock.patch(CHAMAR, side_effect=[None, RuntimeError("seed quebrou")]):
            with self.assertRaises(RuntimeError):
                call_command("preparar_producao", stdout=StringIO())
        self.assertFalse(self.marcador.exists())