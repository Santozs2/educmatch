import json
from unittest import mock

from django.test import SimpleTestCase, override_settings

from quiz.delivery import build_payload, deliver
from quiz.llm import FakeProvider, LLMProvider, LLMResponse, LLMUnavailable, get_provider
from quiz.tests.base import BaseEducMatch


class FakeProviderTest(SimpleTestCase):
    """Passo 7: o dublê respeita o contrato de saída sem tocar a rede."""

    def test_segue_o_protocolo(self):
        self.assertIsInstance(FakeProvider(), LLMProvider)

    def test_entrega_os_ids_na_ordem_recebida(self):
        prompt = json.dumps({"candidatos": [{"course_id": 7}, {"course_id": 3}, {"course_id": 11}]})

        resposta = FakeProvider().complete(prompt)
        saida = json.loads(resposta.text)

        self.assertIsInstance(resposta, LLMResponse)
        self.assertEqual(resposta.model, "fake")
        self.assertEqual(saida["principal"]["course_id"], 7)
        self.assertEqual([a["course_id"] for a in saida["alternativas"]], [3, 11])
        self.assertTrue(all(a["texto"] for a in saida["alternativas"]))

    def test_acha_os_ids_no_meio_de_um_prompt_em_texto(self):
        prompt = '# DADOS\n[{"course_id": 2}, {"course_id":5}]\n# REGRAS\n... "course_id": 2 ...'

        saida = json.loads(FakeProvider().complete(prompt).text)

        self.assertEqual(saida["principal"]["course_id"], 2)
        self.assertEqual([a["course_id"] for a in saida["alternativas"]], [5])

    def test_prompt_sem_curso_e_erro_da_camada(self):
        with self.assertRaises(LLMUnavailable):
            FakeProvider().complete("sem candidatos")


class GetProviderTest(SimpleTestCase):
    @override_settings(LLM_PROVIDER="fake")
    def test_fake(self):
        self.assertIsInstance(get_provider(), FakeProvider)

    # Um nome que não existe: com "gemini", o teste dependia do LLM_MODEL do .env
    @override_settings(LLM_PROVIDER="nao-existe")
    def test_provedor_ainda_nao_implementado_e_erro_da_camada(self):
        with self.assertRaises(LLMUnavailable):
            get_provider()


class BuildPayloadTest(BaseEducMatch):
    """Passo 7: o JSON de entrada do contrato."""

    def test_candidatos_seguem_a_ordem_da_engine(self):
        tentativa = self.criar_tentativa()
        payload = build_payload(tentativa)

        esperados = list(
            tentativa.recomendacoes.order_by("rank_engine").values_list("curso_id", flat=True)
        )
        self.assertEqual([c["course_id"] for c in payload["candidatos"]], esperados)
        self.assertEqual([c["rank_engine"] for c in payload["candidatos"]], [1, 2, 3, 4, 5])

    def test_cada_candidato_tem_os_campos_do_contrato(self):
        candidato = build_payload(self.criar_tentativa())["candidatos"][0]

        self.assertEqual(
            set(candidato),
            {"course_id", "nome", "descricao", "score", "rank_engine", "top_areas"},
        )
        self.assertTrue(candidato["top_areas"])
        self.assertEqual(set(candidato["top_areas"][0]), {"area_name", "percentual"})

    def test_perfil_traz_ate_tres_areas_da_mais_forte_para_a_mais_fraca(self):
        areas = build_payload(self.criar_tentativa())["perfil"]["areas_fortes"]

        self.assertTrue(1 <= len(areas) <= 3)
        pontuacoes = [a["pontuacao"] for a in areas]
        self.assertEqual(pontuacoes, sorted(pontuacoes, reverse=True))
        self.assertTrue(all(a["area_name"] for a in areas))

    def test_tie_set_vai_junto_e_so_tem_candidatos(self):
        payload = build_payload(self.criar_tentativa())

        ids = {c["course_id"] for c in payload["candidatos"]}
        self.assertTrue(payload["tie_set"])
        self.assertLessEqual(set(payload["tie_set"]), ids)

    def test_nao_leva_dado_pessoal(self):
        dono = self.criar_usuario(email="maria.souza@exemplo.com", first_name="Maria")
        tentativa = self.criar_tentativa(dono=dono)
        tentativa.respondido_por = "Maria Souza"
        tentativa.save(update_fields=["respondido_por"])

        texto = json.dumps(build_payload(tentativa), ensure_ascii=False)

        self.assertNotIn("Maria", texto)
        self.assertNotIn("maria.souza", texto)


class EntregaTest(BaseEducMatch):
    @override_settings(LLM_ENABLED=False)
    def test_desligada_nao_chama_nenhum_provedor(self):
        tentativa = self.criar_tentativa()
        with mock.patch("quiz.delivery.get_provider") as provedor:
            self.assertIsNone(deliver(tentativa))
        provedor.assert_not_called()

    @override_settings(LLM_ENABLED=True, LLM_PROVIDER="fake")
    def test_ligada_com_fake_devolve_os_cinco_candidatos(self):
        tentativa = self.criar_tentativa()

        entrega = deliver(tentativa)

        entregues = entrega.ordem
        esperados = list(
            tentativa.recomendacoes.order_by("rank_engine").values_list("curso_id", flat=True)
        )
        self.assertEqual(entregues, esperados)

    @override_settings(LLM_ENABLED=True, LLM_PROVIDER="fake")
    def test_nao_muda_nada_no_banco(self):
        tentativa = self.criar_tentativa()
        antes = list(tentativa.recomendacoes.values_list("curso_id", "rank_final", "llm_text"))

        deliver(tentativa)

        depois = list(tentativa.recomendacoes.values_list("curso_id", "rank_final", "llm_text"))
        self.assertEqual(antes, depois)

    @override_settings(LLM_ENABLED=True, LLM_PROVIDER="fake")
    def test_tentativa_sem_recomendacao_nao_chama_o_provedor(self):
        from quiz.models import Tentativa_de_resposta

        vazia = Tentativa_de_resposta.objects.create(respondido_por="")
        with mock.patch("quiz.delivery.get_provider") as provedor:
            self.assertIsNone(deliver(vazia))
        provedor.assert_not_called()