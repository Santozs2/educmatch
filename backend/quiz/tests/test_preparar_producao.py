import tempfile
from io import StringIO
from pathlib import Path
from unittest import mock

from django.conf import settings
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


class MarcadorConfiguradoTest(SimpleTestCase):
    """O setting existe com o nome que o comando lê. Os outros testes passam o
    valor por override_settings e, por isso, não pegaram o "MARACADOR" que
    derrubou o boot em produção (29/10/2026)."""

    def test_settings_tem_o_marcador_com_o_nome_que_o_comando_le(self):
        self.assertTrue(settings.MARCADOR_PREPARO.endswith(".versao-preparada"))

    def test_comando_roda_sem_override_do_marcador(self):
        # Lê o settings.MARCADOR_PREPARO de verdade; o Path vira dublê só para não gravar no repositório.
        with override_settings(VERSAO="dev"), mock.patch(CHAMAR),                 mock.patch("quiz.management.commands.preparar_producao.Path") as caminho:
            call_command("preparar_producao", stdout=StringIO())
        caminho.assert_called_once_with(settings.MARCADOR_PREPARO)
