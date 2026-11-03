from django.conf import settings

from quiz.llm.base import (
    LLMError, LLMInvalidOutput, LLMProvider, LLMResponse, LLMTimeout, LLMUnavailable,
)
from quiz.llm.fake import FakeProvider
from quiz.llm.openai_compat import OpenAICompatProvider, gemini

__all__ = [
    "FakeProvider", "LLMError", "LLMInvalidOutput", "LLMProvider", "LLMResponse", "LLMTimeout",
    "LLMUnavailable", "OpenAICompatProvider", "get_provider",
]

PROVIDERS = {
    "fake": FakeProvider,
    "openai_compat": OpenAICompatProvider,
    "gemini": gemini,
}


def get_provider(timeout=None) -> LLMProvider:
    """O provedor escolhido em LLM_PROVIDER, no .env.

    timeout troca o LLM_TIMEOUT só nesta instância: o consultor do painel pode
    esperar mais que o aluno no quiz.
    """
    try:
        fabrica = PROVIDERS[settings.LLM_PROVIDER]
    except KeyError:
        raise LLMUnavailable(f"provedor não implementado: {settings.LLM_PROVIDER!r}") from None
    return fabrica() if timeout is None else fabrica(timeout=timeout)
