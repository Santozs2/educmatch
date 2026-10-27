import json
from unittest import mock

from django.test import SimpleTestCase, override_settings

from quiz.delivery import build_payload, deliver
from quiz.llm import LLMInvalidOutput, LLMResponse, LLMUnavailable
from quiz.prompt import carregar, montar_prompt
from quiz.serializers import LIMITE_ALTERNATIVA, LIMITE_PRINCIPAL, validate_delivery
from quiz.tests.base import BaseEducMatch

# Um payload pequeno, à mão: os testes de validação não precisam de banco.
PAYLOAD = {
    "perfil": {"areas_fortes": [{"area": "eletrica", "area_name": "Elétrica", "pontuacao": 18.0}]},
    "candidatos": [
        {"course_id": i, "nome": f"Curso {i}", "descricao": "…", "score": 0.9, "rank_engine": r, "top_areas": []}
        for r, i in enumerate([19, 16, 2, 11, 1], start=1)
    ],
    "tie_set": [19, 16],
}


def saida(principal=19, alternativas=(16, 2, 11, 1), texto="Um texto curto.", texto_principal=None):
    return json.dumps({
        "principal": {"course_id": principal, "texto": texto_principal or texto},
        "alternativas": [{"course_id": i, "texto": texto} for i in alternativas],
    })


class PromptV1Test(SimpleTestCase):
    """Passo 8: o prompt é arquivo, com os quatro blocos e os dados no lugar."""

    def test_arquivo_tem_os_quatro_blocos(self):
        texto = carregar("v1")
        for bloco in ("# PAPEL", "# DADOS", "# REGRAS", "# FORMATO DE SAÍDA"):
            with self.subTest(bloco=bloco):
                self.assertIn(bloco, texto)

    def test_montar_preenche_todos_os_placeholders(self):
        prompt = montar_prompt(PAYLOAD, "v1")

        self.assertNotIn("{{", prompt)
        self.assertIn('"course_id": 19', prompt)
        self.assertIn('"area_name": "Elétrica"', prompt)
        self.assertIn("[\n  19,\n  16\n]", prompt)  # o tie_set, no bloco DADOS

    def test_versao_que_nao_existe_e_erro_da_camada(self):
        with self.assertRaises(LLMUnavailable):
            montar_prompt(PAYLOAD, "v99")

    def test_versao_com_caminho_e_recusada(self):
        with self.assertRaises(LLMUnavailable):
            carregar("../settings")


class PromptV2Test(SimpleTestCase):
    """A v2 traz o critério de desempate e fixa a ordem das alternativas."""

    def test_arquivo_tem_os_blocos_e_o_criterio(self):
        texto = carregar("v2")
        for bloco in ("# PAPEL", "# DADOS", "# CRITÉRIO DE DESEMPATE", "# REGRAS", "# FORMATO DE SAÍDA"):
            with self.subTest(bloco=bloco):
                self.assertIn(bloco, texto)
        self.assertNotIn("respeite a ordem recebida", texto)

    def test_montar_preenche_todos_os_placeholders(self):
        prompt = montar_prompt(PAYLOAD, "v2")

        self.assertNotIn("{{", prompt)
        self.assertIn('"course_id": 19', prompt)
        self.assertIn("[
  19,
  16
]", prompt)


@override_settings(LLM_ENABLED=True, LLM_PROVIDER="fake", LLM_PROMPT_VERSION="v2")
class DeliverComPromptV2Test(BaseEducMatch):
    def test_fake_atravessa_o_prompt_v2_e_a_validacao(self):
        tentativa = self.criar_tentativa()

        entrega = deliver(tentativa)

        self.assertEqual(entrega.ordem, [c["course_id"] for c in build_payload(tentativa)["candidatos"]])


class ValidacaoDaSaidaTest(SimpleTestCase):
    """Passo 8: as regras do contrato de saída, uma por teste."""

    def test_saida_valida_vira_entrega(self):
        entrega = validate_delivery(saida(), PAYLOAD)

        self.assertEqual(entrega.ordem, [19, 16, 2, 11, 1])
        self.assertEqual(entrega.textos[19], "Um texto curto.")

    def test_principal_trocado_dentro_do_tie_set_e_aceito(self):
        entrega = validate_delivery(saida(principal=16, alternativas=(19, 2, 11, 1)), PAYLOAD)
        self.assertEqual(entrega.ordem[0], 16)

    def test_cerca_de_codigo_e_tolerada(self):
        entrega = validate_delivery("```json\n" + saida() + "\n```", PAYLOAD)
        self.assertEqual(entrega.ordem[0], 19)

    def test_recusas(self):
        casos = {
            "JSON quebrado": '{"principal": {"course_id": 19,',
            "sem JSON": "Desculpe, não consigo ajudar.",
            "objeto sem os campos do contrato": '{"ordem": [19, 16, 2, 11, 1]}',
            "curso inventado": saida(alternativas=(16, 2, 11, 999)),
            "curso repetido": saida(alternativas=(16, 2, 11, 16)),
            "só 3 alternativas": saida(alternativas=(16, 2, 11)),
            "texto vazio": saida(texto="   "),
            "principal fora do tie_set": saida(principal=2, alternativas=(19, 16, 11, 1)),
            "principal longo demais": saida(texto_principal="x" * (LIMITE_PRINCIPAL + 1)),
            "alternativa longa demais": saida(texto="x" * (LIMITE_ALTERNATIVA + 1)),
            "id que não é número": saida().replace('"course_id": 19', '"course_id": "dezenove"'),
        }
        for nome, texto in casos.items():
            with self.subTest(nome):
                with self.assertRaises(LLMInvalidOutput):
                    validate_delivery(texto, PAYLOAD)


class LixoProposital:
    """Provedor que devolve uma resposta fora do contrato."""

    name = "lixo"

    def complete(self, prompt):
        return LLMResponse(text='{"principal": {"course_id": 999, "texto": "curso inventado"}}', model="lixo")


@override_settings(LLM_ENABLED=True, LLM_PROVIDER="fake", LLM_PROMPT_VERSION="v1")
class DeliverComPromptTest(BaseEducMatch):
    def test_fake_atravessa_o_prompt_v1_e_a_validacao(self):
        tentativa = self.criar_tentativa()

        entrega = deliver(tentativa)

        esperados = [c["course_id"] for c in build_payload(tentativa)["candidatos"]]
        self.assertEqual(entrega.ordem, esperados)
        self.assertTrue(all(entrega.textos.values()))

    def test_lixo_do_provedor_vira_erro_e_nao_grava_nada(self):
        tentativa = self.criar_tentativa()
        antes = list(tentativa.recomendacoes.values_list("curso_id", "rank_final", "llm_text"))

        with mock.patch("quiz.delivery.get_provider", return_value=LixoProposital()):
            with self.assertRaises(LLMInvalidOutput):
                deliver(tentativa)

        depois = list(tentativa.recomendacoes.values_list("curso_id", "rank_final", "llm_text"))
        self.assertEqual(antes, depois)

    def test_prompt_enviado_nao_leva_dado_pessoal(self):
        tentativa = self.criar_tentativa()
        tentativa.respondido_por = "Maria Souza"
        tentativa.save(update_fields=["respondido_por"])
        enviado = {}

        class Espiao(LixoProposital):
            def complete(self, prompt):
                enviado["prompt"] = prompt
                return super().complete(prompt)

        with mock.patch("quiz.delivery.get_provider", return_value=Espiao()):
            with self.assertRaises(LLMInvalidOutput):
                deliver(tentativa)

        self.assertIn("# REGRAS", enviado["prompt"])
        self.assertNotIn("Maria", enviado["prompt"])