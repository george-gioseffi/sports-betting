"""Abstract base for LLM providers."""
from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field


@dataclass
class LLMResponse:
    """Structured response from an LLM call."""

    classification: str  # green | red | void | unknown | review_manual
    confidence: float  # 0.0 - 1.0
    explanation: str
    raw_response: str = ""
    provider: str = ""
    model: str = ""
    error: str = ""

    @property
    def is_error(self) -> bool:
        return bool(self.error)


SYSTEM_PROMPT = """Voce e um auditor de apostas esportivas. Seu trabalho e analisar apostas
para determinar se o resultado registrado na planilha esta correto, ambiguo ou suspeito.

REGRAS:
- Voce NAO pode inventar resultados esportivos.
- Voce NAO pode determinar se uma aposta ganhou ou perdeu sem evidencia.
- Voce so pode classificar como green/red/void quando ha informacao suficiente.
- Para casos ambiguos, classifique como 'review_manual'.
- Explique seu raciocinio de forma concisa.

Responda APENAS no formato JSON:
{"classification": "green|red|void|unknown|review_manual", "confidence": 0.0-1.0, "explanation": "..."}
"""


class BaseLLMProvider(ABC):
    """Contract for LLM providers."""

    @abstractmethod
    def classify(self, prompt: str) -> LLMResponse:
        """Send a classification prompt and return structured response."""

    @abstractmethod
    def name(self) -> str:
        """Provider name."""

    @abstractmethod
    def model_id(self) -> str:
        """Model identifier used."""

    @abstractmethod
    def available(self) -> bool:
        """Whether this provider has a valid API key and is usable."""
