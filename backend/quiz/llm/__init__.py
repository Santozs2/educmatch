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


def get_provider() -> LLMProvider:
    """O provedor escolhido em LLM_PROVIDER, no .env."""
    try:
        return PROVIDERS[settings.LLM_PROVIDER]()
    except KeyError:
        raise LLMUnavailable(f"provedor não implementado: {settings.LLM_PROVIDER!r}") from None
