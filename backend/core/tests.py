from django.conf import settings
from django.db import connection
from django.test import SimpleTestCase, TestCase


class FusoDoMySQL(TestCase):
    """Com TIME_ZONE fora de UTC, o Django converte fuso DENTRO do SQL
    (CONVERT_TZ). Sem as tabelas de fuso, a conversão devolve NULL e todo
    filtro por __date, __month ou TruncDate volta vazio, sem erro."""

    def test_mysql_conhece_o_fuso_de_sao_paulo(self):
        with connection.cursor() as cursor:
            cursor.execute("select CONVERT_TZ(NOW(), 'UTC', %s)", [settings.TIME_ZONE])
            convertido = cursor.fetchone()[0]

        self.assertIsNotNone(
            convertido,
            "as tabelas de fuso do MySQL estao vazias: veja o README, secao 'Tabelas de fuso'",
        )
        

class CacheNoBanco(TestCase):
    """PRE-03: o cache da LLM tem de sobreviver a um reinício do servidor."""

    def test_cache_e_de_banco_e_a_tabela_existe(self):
        from django.core.cache import cache

        self.assertEqual(
            settings.CACHES["default"]["BACKEND"],
            "django.core.cache.backends.db.DatabaseCache",
        )
        cache.set("pre-ia", "ok", 30)
        self.assertEqual(cache.get("pre-ia"), "ok")


class ConfiguracaoDaLLM(TestCase):
    def test_variaveis_existem_com_o_tipo_certo(self):
        self.assertIsInstance(settings.LLM_ENABLED, bool)
        self.assertIn(settings.LLM_PROVIDER, {"fake", "gemini", "openai_compat"})
        self.assertIsInstance(settings.LLM_TIMEOUT, float)
        self.assertTrue(settings.LLM_PROMPT_VERSION)


class OpcoesDoSQLite(SimpleTestCase):
    """U1: com threads, o SQLite espera a vez em vez de perder a gravação.

    A CI roda em MySQL, então este teste confere a configuração, e não o
    comportamento. O comportamento em si é medido pelo teste de carga
    (scripts/carga_turma.py) com DB_ENGINE=sqlite.
    """

    def test_transacao_imediata_com_espera(self):
        self.assertEqual(settings.SQLITE_OPTIONS["transaction_mode"], "IMMEDIATE")
        self.assertGreaterEqual(settings.SQLITE_OPTIONS["timeout"], 10)
