import unittest

from django.test import SimpleTestCase

from accounts.models import Interesse
from quiz.models import Recomendacao, Tentativa_de_resposta


class ConformidadeDosContratos(SimpleTestCase):
    """Um teste por contrato. A saida de `manage.py test -v 2` E a tabela
    de conformidade -- gerada, nao afirmada.

    Contrato ainda nao implementado usa `skip` com a razao. Skip aparece no
    relatorio a cada execucao, entao a pendencia fica visivel em vez de
    silenciosa -- que foi exatamente o problema da v0.1.
    """

    @unittest.skip("C1: build_payload chega com o Passo 7 da camada de IA")
    def test_c1_build_payload_existe_e_tem_os_campos_do_contrato(self):
        from quiz.engine import build_payload  # noqa

    @unittest.skip("C2: saida da LLM e as 5 regras chegam com o Passo 8")
    def test_c2_saida_da_llm_passa_pelas_cinco_regras(self):
        pass

    @unittest.skip("C3: endpoint de entrega chega com a F2-09")
    def test_c3_endpoint_de_entrega_responde_no_formato_do_contrato(self):
        pass

    def test_c4_interesse_tem_os_tres_campos_de_snapshot(self):
        campos = {f.name for f in Interesse._meta.get_fields()}
        for exigido in ("afinidade_snapshot", "rank_snapshot", "era_principal"):
            with self.subTest(campo=exigido):
                self.assertIn(exigido, campos)

    def test_c4_garantias_estruturais_continuam_de_pe(self):
        """PROTECT no curso, SET_NULL na tentativa, unico por (usuario, curso)."""
        curso = Interesse._meta.get_field("curso")
        origem = Interesse._meta.get_field("tentativa_origem")

        self.assertEqual(curso.remote_field.on_delete.__name__, "PROTECT")
        self.assertEqual(origem.remote_field.on_delete.__name__, "SET_NULL")
        self.assertTrue(
            any(
                set(getattr(c, "fields", [])) == {"usuario", "curso"}
                for c in Interesse._meta.constraints
            )
        )

    def test_c4_criado_em_nao_e_auto_now(self):
        """REV-01: a diferenca de uma palavra que invalidava a serie temporal."""
        campo = Interesse._meta.get_field("criado_em")
        self.assertTrue(campo.auto_now_add)
        self.assertFalse(campo.auto_now)

    def test_c6_o_claim_esta_conectado(self):
        """Sem o import no ready() do AppConfig, o receiver nao existe."""
        from django.contrib.auth.signals import user_logged_in

        registrados = [r[1]() for r in user_logged_in.receivers]
        nomes = {getattr(f, "__name__", "") for f in registrados if f}
        self.assertIn("adotar_tentativas_da_sessao", nomes)