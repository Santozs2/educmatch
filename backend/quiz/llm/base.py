from dataclasses import dataclass
from typing import Protocol, runtime_checkable


class LLMError(Exception):
    """Qualquer falha da camada de IA. É transformada em fallback."""


class LLMTimeout(LLMError):
    """O provedor passou de LLM_TIMEOUT segundos."""


class LLMUnavailable(LLMError):
    """Sem provedor: nome desconhecido, sem chave, sem crédito ou sem rede."""

class LLMInvalidOutput(LLMError):
    """A resposta chegou, mas quebra o contrato de saída (Passo 8)."""

@dataclass(frozen=True)
class LLMResponse:
    """O que todo provedor devolve. Os números vão para a Tentativa."""

    text: str
    model: str
    tokens_in: int | None = None
    tokens_out: int | None = None


@runtime_checkable
class LLMProvider(Protocol):
    name: str

    def complete(self, prompt: str) -> LLMResponse: ...