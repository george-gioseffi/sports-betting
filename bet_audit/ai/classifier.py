"""AI Classifier — orchestrates LLM calls for ambiguous bets."""
from __future__ import annotations

import logging

from bet_audit.ai.base_llm import BaseLLMProvider, LLMResponse
from bet_audit.config import AuditConfig

logger = logging.getLogger(__name__)


def _build_prompt(row: dict) -> str:
    parts = [
        "Analise esta aposta e determine se o resultado registrado esta correto:",
        f"  Descricao: {row.get('descricao', '')}",
        f"  Casa: {row.get('casa', '')}",
        f"  Status original: {row.get('status_original', '')}",
        f"  Lucro: {row.get('lucro', '')}",
        f"  Odd: {row.get('odd', '')}",
        f"  Data: {row.get('data', '')}",
    ]
    if row.get("resultado_externo"):
        parts.append(f"  Resultado externo: {row['resultado_externo']}")
    if row.get("motivo_externo"):
        parts.append(f"  Motivo externo: {row['motivo_externo']}")
    if row.get("resultado_norm"):
        parts.append(f"  Resultado determinístico: {row['resultado_norm']}")

    parts.append("")
    parts.append("Classifique como: green, red, void, unknown, ou review_manual.")
    return "\n".join(parts)


class AIClassifier:
    """Manages LLM classification of ambiguous bets."""

    def __init__(self, config: AuditConfig, providers: list[BaseLLMProvider] | None = None) -> None:
        self._config = config
        self._providers = providers or []
        self._calls_made = 0

    @property
    def calls_made(self) -> int:
        return self._calls_made

    @property
    def budget_remaining(self) -> int:
        return max(0, self._config.max_llm_calls - self._calls_made)

    def available(self) -> bool:
        return self._config.llm_enabled and any(p.available() for p in self._providers)

    def classify(self, row: dict) -> LLMResponse:
        """Classify a single bet row. Returns best result from available providers."""
        if not self._config.llm_enabled:
            return LLMResponse(
                classification="unknown",
                confidence=0.0,
                explanation="LLM mode is off",
                provider="none",
            )

        if self._calls_made >= self._config.max_llm_calls:
            return LLMResponse(
                classification="unknown",
                confidence=0.0,
                explanation="LLM call budget exhausted",
                provider="none",
                error="budget_exhausted",
            )

        prompt = _build_prompt(row)
        best: LLMResponse | None = None

        for provider in self._providers:
            if not provider.available():
                continue

            self._calls_made += 1
            result = provider.classify(prompt)

            if result.is_error:
                logger.warning("LLM provider %s error: %s", provider.name(), result.error)
                continue

            if best is None or result.confidence > best.confidence:
                best = result

            if self._config.llm_provider != "dual":
                break

        if best is None:
            return LLMResponse(
                classification="unknown",
                confidence=0.0,
                explanation="no LLM provider available or all failed",
                provider="none",
                error="all_providers_failed",
            )

        return best

    def should_classify(self, row: dict) -> bool:
        """Decide whether this row needs AI classification."""
        mode = self._config.llm_mode
        if mode == "off":
            return False
        if not self.available():
            return False
        if self.budget_remaining <= 0:
            return False

        if mode == "review_all_suspects":
            return row.get("is_suspect", False) or row.get("resultado_norm") == "unknown"
        if mode == "assisted":
            return row.get("resultado_norm") == "unknown"
        if mode == "dual_review":
            return row.get("is_suspect", False)
        return False
