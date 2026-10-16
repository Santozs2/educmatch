import json

from django.test import SimpleTestCase, override_settings

from accounts.models import Interesse
from quiz.delivery import build_payload
from quiz.llm import LLMInvalidOutput
from quiz.models import Recomendacao, Tentativa_de_resposta
from quiz.serializers import LIMITE_PRINCIPAL, validate_delivery
from quiz.tests.base import BaseEducMatch


class ConformidadeDosContratos(SimpleTestCase):
    """Um teste por contrato. A saida de `manage.py test -v 2` E a tabela
    de conformidade -- gerada, nao afirmada.

    Contrato ainda nao implementado usa `skip` com a razao. Skip aparece no
    relatorio a cada execucao, entao a pendencia fica visivel em vez de
    silenciosa -- que foi exatamente o problema da v0.1.
    """

    def test_c2_saida_da_llm_passa_pelas_cinco_regras(self):
        """Passo 8: a saida da LLM so entra no banco se cumprir as 5 regras."""
        payload = {"candidatos": [{"course_id": i} for i in (1, 2, 3, 4, 5)], "tie_set": [1, 2]}

        def saida(principal=1, alternativas=(2, 3, 4, 5), texto="Texto."):
            return json.dumps({
                "principal": {"course_id": principal, "texto": texto},
                "alternativas": [{"course_id": i, "texto": "Alternativa."} for i in alternativas],
            })

        self.assertEqual(validate_delivery(saida(), payload).ordem, [1, 2, 3, 4, 5])
        quebras = {
            "1. curso fora da lista": saida(alternativas=(2, 3, 4, 99)),
            "2. curso repetido": saida(alternativas=(2, 3, 4, 4)),
            "3. candidato descartado": saida(alternativas=(2, 3, 4)),
            "4. principal fora do tie_set": saida(principal=3, alternativas=(1, 2, 4, 5)),
            "5. texto acima do limite": saida(texto="x" * (LIMITE_PRINCIPAL + 1)),
        }
        for regra, texto in quebras.items():
            with self.subTest(regra), self.assertRaises(LLMInvalidOutput):
                validate_delivery(texto, payload)

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


class ConformidadeDosContratosComBanco(BaseEducMatch):
    """Os contratos que precisam de uma tentativa de verdade no banco."""

    def test_c1_build_payload_existe_e_tem_os_campos_do_contrato(self):
        payload = build_payload(self.criar_tentativa())

        self.assertEqual(set(payload), {"perfil", "candidatos", "tie_set"})
        self.assertEqual(set(payload["perfil"]), {"areas_fortes"})
        for area in payload["perfil"]["areas_fortes"]:
            self.assertEqual(set(area), {"area", "area_name", "pontuacao"})
        self.assertEqual(len(payload["candidatos"]), 5)
        for candidato in payload["candidatos"]:
            self.assertEqual(
                set(candidato),
                {"course_id", "nome", "descricao", "score", "rank_engine", "top_areas"},
            )
        self.assertLessEqual(set(payload["tie_set"]), {c["course_id"] for c in payload["candidatos"]})

    @override_settings(LLM_ENABLED=True, LLM_PROVIDER="fake", LLM_MODEL="", LLM_PROMPT_VERSION="v1")
    def test_c3_entrega_chega_ao_aluno_no_post_do_quiz(self):
        """C3 nasceu como endpoint (F2-09). O Passo 9 trocou por uma etapa so:
        a entrega acontece no POST do quiz e o aluno ja abre o resultado com o texto."""
        resposta = self.responder_tudo()

        self.assertEqual(resposta.status_code, 302)
        tentativa = Tentativa_de_resposta.objects.latest("id")
        self.assertFalse(tentativa.used_fallback)
        self.assertTrue(all(rec.llm_text for rec in tentativa.recomendacoes.all()))
        pagina = self.client.get(resposta.url)
        self.assertContains(pagina, "Texto escrito com IA")
        self.assertContains(pagina, tentativa.recomendacoes.get(rank_final=1).llm_text)
