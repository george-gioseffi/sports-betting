"""Anthropic LLM provider."""
from __future__ import annotations

import json
import logging

from anthropic import Anthropic, AuthenticationError, RateLimitError, APIConnectionError, APITimeoutError

from bet_audit.ai.base_llm import SYSTEM_PROMPT, BaseLLMProvider, LLMResponse

logger = logging.getLogger(__name__)

DEFAULT_MODEL = "claude-haiku-4-5-20251001"


class AnthropicProvider(BaseLLMProvider):
    def __init__(self, api_key: str | None = None, model: str = DEFAULT_MODEL, timeout: float = 30.0) -> None:
        self._api_key = api_key
        self._model = model
        self._timeout = timeout
        self._client: Anthropic | None = None

    def name(self) -> str:
        return "anthropic"

    def model_id(self) -> str:
        return self._model

    def available(self) -> bool:
        return bool(self._api_key)

    def _get_client(self) -> Anthropic | None:
        if self._client is None and self._api_key:
            self._client = Anthropic(api_key=self._api_key, timeout=self._timeout)
        return self._client

    def classify(self, prompt: str) -> LLMResponse:
        if not self.available():
            return LLMResponse(
                classification="unknown", confidence=0.0, explanation="",
                error="Anthropic API key not configured", provider=self.name(), model=self._model,
            )

        client = self._get_client()
        if client is None:
            return LLMResponse(
                classification="unknown", confidence=0.0, explanation="",
                error="failed to create Anthropic client", provider=self.name(), model=self._model,
            )

        try:
            response = client.messages.create(
                model=self._model,
                max_tokens=300,
                system=SYSTEM_PROMPT,
                messages=[{"role": "user", "content": prompt}],
            )
            raw = response.content[0].text if response.content else ""
            return self._parse(raw)

        except AuthenticationError as e:
            logger.warning("Anthropic auth failed: %s", e)
            return LLMResponse(
                classification="unknown", confidence=0.0, explanation="",
                error=f"auth_error: {e}", provider=self.name(), model=self._model,
            )
        except RateLimitError as e:
            logger.warning("Anthropic rate limit: %s", e)
            return LLMResponse(
                classification="unknown", confidence=0.0, explanation="",
                error=f"rate_limit: {e}", provider=self.name(), model=self._model,
            )
        except APITimeoutError as e:
            logger.warning("Anthropic timeout: %s", e)
            return LLMResponse(
                classification="unknown", confidence=0.0, explanation="",
                error=f"timeout: {e}", provider=self.name(), model=self._model,
            )
        except APIConnectionError as e:
            logger.warning("Anthropic connection error: %s", e)
            return LLMResponse(
                classification="unknown", confidence=0.0, explanation="",
                error=f"connection_error: {e}", provider=self.name(), model=self._model,
            )
        except Exception as e:
            logger.warning("Anthropic unexpected error: %s", e)
            return LLMResponse(
                classification="unknown", confidence=0.0, explanation="",
                error=f"unexpected: {e}", provider=self.name(), model=self._model,
            )

    def _parse(self, raw: str) -> LLMResponse:
        try:
            raw_clean = raw.strip()
            if raw_clean.startswith("```"):
                raw_clean = raw_clean.split("\n", 1)[1].rsplit("```", 1)[0].strip()
            data = json.loads(raw_clean)
            classification = str(data.get("classification", "unknown")).lower().strip()
            if classification not in ("green", "red", "void", "unknown", "review_manual"):
                classification = "unknown"
            return LLMResponse(
                classification=classification,
                confidence=max(0.0, min(1.0, float(data.get("confidence", 0.0)))),
                explanation=str(data.get("explanation", "")),
                raw_response=raw,
                provider=self.name(),
                model=self._model,
            )
        except (json.JSONDecodeError, ValueError, TypeError):
            return LLMResponse(
                classification="unknown", confidence=0.0,
                explanation=raw[:200], raw_response=raw,
                provider=self.name(), model=self._model,
                error="failed to parse LLM JSON response",
            )
