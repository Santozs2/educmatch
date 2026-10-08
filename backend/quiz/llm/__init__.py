from django.conf import settings

from quiz.llm.base import LLMError, LLMProvider, LLMResponse, LLMTimeout, LLMUnavailable
from quiz.llm.fake import FakeProvider

__all__ = [
    "FakeProvider", "LLMError", "LLMProvider", "LLMResponse", "LLMTimeout",
    "LLMUnavailable", "get_provider",
]

PROVIDERS = {
    "fake": FakeProvider,
}


def get_provider() -> LLMProvider:
    """O provedor escolhido em LLM_PROVIDER, no .env."""
    try:
        return PROVIDERS[settings.LLM_PROVIDER]()
    except KeyError:
        raise LLMUnavailable(f"provedor não implementado: {settings.LLM_PROVIDER!r}") from None