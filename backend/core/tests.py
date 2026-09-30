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

        self.assertIsNotNone(convertido, "as tabelas de fuso do MySQL estao vazias: veja o README, secao -Tabelas de fuso-")