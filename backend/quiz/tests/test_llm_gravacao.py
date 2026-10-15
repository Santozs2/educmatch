import json
from unittest import mock

from django.test import override_settings

from quiz.delivery import entregar
from quiz.llm import FakeProvider, LLMResponse, LLMTimeout
from quiz.models import Tentativa_de_resposta
from quiz.tests.base import BaseEducMatch

PROVEDOR = "quiz.delivery.get_provider"


class Roteiro:
    """Provedor de teste que conta as chamadas e responde o que o teste mandar."""

    name = "roteiro"

    def __init__(self, responder=None, erro=None):
        self.chamadas = 0
        self.responder = responder
        self.erro = erro

    def complete(self, prompt):
        self.chamadas += 1
        if self.erro:
            raise self.erro
        if self.responder:
            return LLMResponse(text=self.responder(), model="roteiro", tokens_in=900, tokens_out=300)
        resposta = FakeProvider().complete(prompt)
        return LLMResponse(text=resposta.text, model="roteiro", tokens_in=900, tokens_out=300)


@override_settings(LLM_ENABLED=True, LLM_PROVIDER="fake", LLM_MODEL="", LLM_PROMPT_VERSION="v1")
class EntregarTest(BaseEducMatch):
    """Passo 9: grava a entrega ou cai na engine, e mede tudo."""

    def ordem_engine(self, tentativa):
        return list(tentativa.recomendacoes.order_by("rank_engine").values_list("curso_id", flat=True))

    def assertOrdemDaEngine(self, tentativa):
        for rec in tentativa.recomendacoes.all():
            self.assertEqual(rec.rank_final, rec.rank_engine)
            self.assertEqual(rec.llm_text, "")

    @override_settings(LLM_ENABLED=False)
    def test_desligada_nao_grava_nada(self):
        tentativa = self.criar_tentativa()

        self.assertFalse(entregar(tentativa))

        tentativa.refresh_from_db()
        self.assertEqual(tentativa.llm_model, "")
        self.assertOrdemDaEngine(tentativa)

    def test_entrega_valida_e_gravada_com_os_metadados(self):
        tentativa = self.criar_tentativa()

        self.assertTrue(entregar(tentativa))

        tentativa.refresh_from_db()
        self.assertTrue(all(rec.llm_text for rec in tentativa.recomendacoes.all()))
        self.assertEqual(tentativa.llm_model, "fake")
        self.assertEqual(tentativa.prompt_version, "v1")
        self.assertIsNotNone(tentativa.latency_ms)
        self.assertFalse(tentativa.used_fallback)
        self.assertFalse(tentativa.diverged)
        self.assertFalse(tentativa.cache_hit)

    def test_troca_dentro_do_tie_set_e_gravada_como_divergencia(self):
        tentativa = self.criar_tentativa()
        primeiro, segundo, *resto = self.ordem_engine(tentativa)
        tentativa.tie_set = [primeiro, segundo]
        tentativa.save(update_fields=["tie_set"])

        def segundo_em_primeiro():
            return json.dumps({
                "principal": {"course_id": segundo, "texto": "Principal."},
                "alternativas": [{"course_id": i, "texto": "Alternativa."} for i in [primeiro, *resto]],
            })

        with mock.patch(PROVEDOR, return_value=Roteiro(responder=segundo_em_primeiro)):
            self.assertTrue(entregar(tentativa))

        tentativa.refresh_from_db()
        trocado = tentativa.recomendacoes.get(curso_id=segundo)
        self.assertEqual((trocado.rank_final, trocado.rank_engine), (1, 2))
        self.assertTrue(trocado.is_primary)
        self.assertTrue(tentativa.diverged)
        self.assertEqual((tentativa.tokens_in, tentativa.tokens_out), (900, 300))

    def test_falhas_caem_na_engine_sem_erro(self):
        casos = {
            "saída inválida": Roteiro(responder=lambda: '{"principal": {"course_id": 999, "texto": "x"}}'),
            "timeout": Roteiro(erro=LLMTimeout("8s")),
            "bug inesperado": Roteiro(erro=RuntimeError("bug")),
        }
        for nome, provedor in casos.items():
            with self.subTest(nome):
                tentativa = self.criar_tentativa()
                with mock.patch(PROVEDOR, return_value=provedor), self.assertLogs("quiz.delivery", "WARNING"):
                    self.assertFalse(entregar(tentativa))

                tentativa.refresh_from_db()
                self.assertTrue(tentativa.used_fallback)
                self.assertFalse(tentativa.diverged)
                self.assertOrdemDaEngine(tentativa)

    def test_mesmo_perfil_sai_do_cache(self):
        provedor = Roteiro()
        with mock.patch(PROVEDOR, return_value=provedor):
            primeira = self.criar_tentativa()
            entregar(primeira)
            segunda = self.criar_tentativa()  # mesmas respostas
            entregar(segunda)

        self.assertEqual(provedor.chamadas, 1)
        segunda.refresh_from_db()
        self.assertTrue(segunda.cache_hit)
        self.assertIsNone(segunda.tokens_in)  # no cache não se gasta token
        self.assertEqual(
            list(segunda.recomendacoes.values_list("llm_text", flat=True)),
            list(primeira.recomendacoes.values_list("llm_text", flat=True)),
        )

    def test_resposta_recusada_nao_entra_no_cache(self):
        lixo = Roteiro(responder=lambda: "não é JSON")
        with mock.patch(PROVEDOR, return_value=lixo), self.assertLogs("quiz.delivery", "WARNING"):
            entregar(self.criar_tentativa())
            entregar(self.criar_tentativa())

        self.assertEqual(lixo.chamadas, 2)

    def test_trocar_o_modelo_nao_reaproveita_o_cache(self):
        provedor = Roteiro()
        with mock.patch(PROVEDOR, return_value=provedor):
            entregar(self.criar_tentativa())
            with self.settings(LLM_MODEL="outro-modelo"):
                entregar(self.criar_tentativa())

        self.assertEqual(provedor.chamadas, 2)


@override_settings(LLM_ENABLED=True, LLM_PROVIDER="fake", LLM_PROMPT_VERSION="v1")
class QuizComLLMTest(BaseEducMatch):
    """Passo 9: o quiz chama a LLM depois da engine, e nunca quebra por causa dela."""

    def test_quiz_grava_a_entrega(self):
        resposta = self.responder_tudo()

        self.assertEqual(resposta.status_code, 302)
        tentativa = Tentativa_de_resposta.objects.latest("id")
        self.assertEqual(tentativa.llm_model, "fake")
        self.assertTrue(all(rec.llm_text for rec in tentativa.recomendacoes.all()))

    def test_provedor_fora_do_ar_nao_quebra_o_quiz(self):
        with mock.patch(PROVEDOR, return_value=Roteiro(erro=LLMTimeout("8s"))), self.assertLogs("quiz.delivery", "WARNING"):
            resposta = self.responder_tudo()

        self.assertEqual(resposta.status_code, 302)
        tentativa = Tentativa_de_resposta.objects.latest("id")
        self.assertTrue(tentativa.used_fallback)
        self.assertEqual(self.client.get(resposta.url).status_code, 200)
