from django.conf import settings
from django.db import connection
from django.test import TestCase


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
        self.assertIn(settings.LLM_PROVIDER, {"gemini", "fake"})
        self.assertIsInstance(settings.LLM_TIMEOUT, float)
        self.assertTrue(settings.LLM_PROMPT_VERSION)