import json
import urllib.error
from unittest import mock

from django.test import SimpleTestCase, override_settings

from quiz.llm import LLMTimeout, LLMUnavailable, OpenAICompatProvider, get_provider
from quiz.llm.openai_compat import GEMINI_BASE_URL

URLOPEN = "quiz.llm.openai_compat.urllib.request.urlopen"


def resposta_http(corpo):
    """O objeto que o urlopen devolve, com o corpo em JSON."""
    resposta = mock.MagicMock()
    resposta.__enter__.return_value.read.return_value = json.dumps(corpo).encode("utf-8")
    return resposta


OK = {
    "model": "gemini-2.5-flash-lite",
    "choices": [{"message": {"content": '{"principal": {}}'}}],
    "usage": {"prompt_tokens": 1200, "completion_tokens": 350},
}


class OpenAICompatProviderTest(SimpleTestCase):
    """Passo 9: o provedor real, com a rede trocada por um dublê."""

    def provedor(self):
        return OpenAICompatProvider(base_url="https://api.exemplo/v1/", model="modelo-x", api_key="chave", timeout=8)

    def test_monta_o_pedido_e_le_a_resposta(self):
        with mock.patch(URLOPEN, return_value=resposta_http(OK)) as urlopen:
            resposta = self.provedor().complete("o prompt")

        pedido = urlopen.call_args.args[0]
        corpo = json.loads(pedido.data)
        self.assertEqual(pedido.full_url, "https://api.exemplo/v1/chat/completions")
        self.assertEqual(pedido.get_header("Authorization"), "Bearer chave")
        self.assertEqual(corpo["model"], "modelo-x")
        self.assertEqual(corpo["temperature"], 0)
        self.assertEqual(corpo["messages"], [{"role": "user", "content": "o prompt"}])
        self.assertEqual(urlopen.call_args.kwargs["timeout"], 8)

        self.assertEqual(resposta.text, '{"principal": {}}')
        self.assertEqual(resposta.model, "gemini-2.5-flash-lite")
        self.assertEqual((resposta.tokens_in, resposta.tokens_out), (1200, 350))

    def test_erros_viram_erros_da_camada(self):
        casos = {
            "cota do plano gratuito (429)": (
                urllib.error.HTTPError("u", 429, "Too Many Requests", {}, None), LLMUnavailable),
            "chave errada (401)": (urllib.error.HTTPError("u", 401, "Unauthorized", {}, None), LLMUnavailable),
            "timeout": (TimeoutError("timed out"), LLMTimeout),
            "timeout ao conectar": (urllib.error.URLError(TimeoutError("timed out")), LLMTimeout),
            "sem internet": (urllib.error.URLError("getaddrinfo failed"), LLMUnavailable),
        }
        for nome, (erro, esperado) in casos.items():
            with self.subTest(nome), mock.patch(URLOPEN, side_effect=erro):
                with self.assertRaises(esperado):
                    self.provedor().complete("o prompt")

    def test_corpo_fora_do_formato_e_erro_da_camada(self):
        with mock.patch(URLOPEN, return_value=resposta_http({"error": "?"})):
            with self.assertRaises(LLMUnavailable):
                self.provedor().complete("o prompt")

    def test_sem_endereco_ou_modelo_nao_monta(self):
        with self.assertRaises(LLMUnavailable):
            OpenAICompatProvider(base_url="", model="modelo-x", api_key="", timeout=8)
        with self.assertRaises(LLMUnavailable):
            OpenAICompatProvider(base_url="https://api.exemplo/v1", model="", api_key="", timeout=8)


class GetProviderRealTest(SimpleTestCase):
    @override_settings(LLM_PROVIDER="gemini", LLM_BASE_URL="", LLM_MODEL="gemini-2.5-flash-lite")
    def test_gemini_sem_endereco_usa_o_do_google(self):
        self.assertEqual(get_provider().base_url, GEMINI_BASE_URL)

    @override_settings(LLM_PROVIDER="openai_compat", LLM_BASE_URL="https://api.groq.com/openai/v1", LLM_MODEL="llama")
    def test_openai_compat_usa_o_endereco_do_env(self):
        self.assertEqual(get_provider().base_url, "https://api.groq.com/openai/v1")
