"""Provedor real: qualquer API no formato /chat/completions da OpenAI.

Gemini, Groq, OpenRouter, OmniRoute e Ollama aceitam esse formato: trocar de
provedor é trocar LLM_BASE_URL, LLM_MODEL e LLM_API_KEY no .env, sem código.
Usa só a biblioteca padrão (urllib): nenhuma dependência nova.
"""
import json
import urllib.error
import urllib.request

from django.conf import settings

from quiz.llm.base import LLMResponse, LLMTimeout, LLMUnavailable

GEMINI_BASE_URL = "https://generativelanguage.googleapis.com/v1beta/openai"
MAX_TOKENS = 2048  # o JSON de saída tem ~1.500 caracteres; sobra para modelos que "pensam"


class OpenAICompatProvider:
    name = "openai_compat"

    def __init__(self, base_url=None, model=None, api_key=None, timeout=None):
        self.base_url = (settings.LLM_BASE_URL if base_url is None else base_url).rstrip("/")
        self.model = settings.LLM_MODEL if model is None else model
        self.api_key = settings.LLM_API_KEY if api_key is None else api_key
        self.timeout = settings.LLM_TIMEOUT if timeout is None else timeout
        if not self.base_url or not self.model:
            raise LLMUnavailable("LLM_BASE_URL e LLM_MODEL são obrigatórios")

    def complete(self, prompt: str) -> LLMResponse:
        corpo = json.dumps({
            "model": self.model,
            "messages": [{"role": "user", "content": prompt}],
            "temperature": 0,
            "max_tokens": MAX_TOKENS,
        }).encode("utf-8")
        pedido = urllib.request.Request(
            f"{self.base_url}/chat/completions",
            data=corpo,
            method="POST",
            headers={"Content-Type": "application/json", "Authorization": f"Bearer {self.api_key}"},
        )
        try:
            with urllib.request.urlopen(pedido, timeout=self.timeout) as resposta:
                dados = json.loads(resposta.read().decode("utf-8"))
        except urllib.error.HTTPError as erro:
            # 401/403 = chave, 429 = cota do plano gratuito, 5xx = provedor fora
            raise LLMUnavailable(f"HTTP {erro.code} do provedor") from None
        except urllib.error.URLError as erro:
            if isinstance(erro.reason, TimeoutError):
                raise LLMTimeout(f"sem resposta em {self.timeout}s") from None
            raise LLMUnavailable(f"sem conexão: {erro.reason}") from None
        except TimeoutError:
            raise LLMTimeout(f"sem resposta em {self.timeout}s") from None
        except (OSError, ValueError) as erro:
            raise LLMUnavailable(f"resposta ilegível: {erro}") from None

        try:
            texto = dados["choices"][0]["message"]["content"]
        except (KeyError, IndexError, TypeError):
            raise LLMUnavailable("a resposta não tem choices[0].message.content") from None
        uso = dados.get("usage") or {}
        return LLMResponse(
            text=texto or "",
            model=dados.get("model") or self.model,
            tokens_in=uso.get("prompt_tokens"),
            tokens_out=uso.get("completion_tokens"),
        )


def gemini():
    """O mesmo provedor, já apontado para o Gemini se LLM_BASE_URL estiver vazio."""
    return OpenAICompatProvider(base_url=settings.LLM_BASE_URL or GEMINI_BASE_URL)
