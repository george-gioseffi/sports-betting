"""Tests for AI provider parsing, error handling, and fallback behavior."""
from __future__ import annotations

from unittest.mock import MagicMock, patch

import pytest

from bet_audit.ai.base_llm import LLMResponse
from bet_audit.ai.openai_provider import OpenAIProvider
from bet_audit.ai.anthropic_provider import AnthropicProvider
from bet_audit.ai.classifier import AIClassifier
from bet_audit.config import AuditConfig


# --------------------------------------------------------------------------- #
#  OpenAI Provider
# --------------------------------------------------------------------------- #
class TestOpenAIProvider:
    def test_not_available_without_key(self):
        p = OpenAIProvider(api_key=None)
        assert not p.available()
        assert p.name() == "openai"
        assert p.model_id() == "gpt-4o-mini"

    def test_classify_without_key_returns_error(self):
        p = OpenAIProvider(api_key=None)
        r = p.classify("test")
        assert r.is_error
        assert r.classification == "unknown"
        assert "not configured" in r.error

    def test_available_with_key(self):
        p = OpenAIProvider(api_key="sk-test")
        assert p.available()

    def test_parse_valid_json(self):
        p = OpenAIProvider(api_key="sk-test")
        raw = '{"classification": "green", "confidence": 0.85, "explanation": "test ok"}'
        r = p._parse(raw)
        assert r.classification == "green"
        assert r.confidence == 0.85
        assert r.explanation == "test ok"
        assert not r.is_error

    def test_parse_markdown_wrapped(self):
        p = OpenAIProvider(api_key="sk-test")
        raw = '```json\n{"classification": "red", "confidence": 0.9, "explanation": "loss"}\n```'
        r = p._parse(raw)
        assert r.classification == "red"
        assert r.confidence == 0.9

    def test_parse_invalid_json(self):
        p = OpenAIProvider(api_key="sk-test")
        r = p._parse("this is not json")
        assert r.is_error
        assert r.classification == "unknown"

    def test_parse_invalid_classification(self):
        p = OpenAIProvider(api_key="sk-test")
        raw = '{"classification": "INVALID", "confidence": 0.5, "explanation": "bad"}'
        r = p._parse(raw)
        assert r.classification == "unknown"

    def test_parse_confidence_clamped(self):
        p = OpenAIProvider(api_key="sk-test")
        raw = '{"classification": "green", "confidence": 1.5, "explanation": "over"}'
        r = p._parse(raw)
        assert r.confidence == 1.0

    def test_parse_negative_confidence(self):
        p = OpenAIProvider(api_key="sk-test")
        raw = '{"classification": "green", "confidence": -0.5, "explanation": "neg"}'
        r = p._parse(raw)
        assert r.confidence == 0.0

    def test_model_field_propagated(self):
        p = OpenAIProvider(api_key="sk-test", model="gpt-4o")
        raw = '{"classification": "green", "confidence": 0.8, "explanation": "ok"}'
        r = p._parse(raw)
        assert r.model == "gpt-4o"
        assert r.provider == "openai"

    def test_auth_error_handled(self):
        p = OpenAIProvider(api_key="sk-invalid")
        p._client = MagicMock()
        from openai import AuthenticationError
        mock_resp = MagicMock()
        mock_resp.status_code = 401
        p._client.chat.completions.create.side_effect = AuthenticationError(
            message="bad key", response=mock_resp, body=None
        )
        r = p.classify("test")
        assert r.is_error
        assert "auth_error" in r.error

    def test_rate_limit_handled(self):
        p = OpenAIProvider(api_key="sk-test")
        p._client = MagicMock()
        from openai import RateLimitError
        mock_resp = MagicMock()
        mock_resp.status_code = 429
        p._client.chat.completions.create.side_effect = RateLimitError(
            message="rate limit", response=mock_resp, body=None
        )
        r = p.classify("test")
        assert r.is_error
        assert "rate_limit" in r.error

    def test_timeout_handled(self):
        p = OpenAIProvider(api_key="sk-test")
        p._client = MagicMock()
        from openai import APITimeoutError
        p._client.chat.completions.create.side_effect = APITimeoutError(request=MagicMock())
        r = p.classify("test")
        assert r.is_error
        assert "timeout" in r.error

    def test_connection_error_handled(self):
        p = OpenAIProvider(api_key="sk-test")
        p._client = MagicMock()
        from openai import APIConnectionError
        p._client.chat.completions.create.side_effect = APIConnectionError(request=MagicMock())
        r = p.classify("test")
        assert r.is_error
        assert "connection_error" in r.error

    def test_successful_mock_call(self):
        p = OpenAIProvider(api_key="sk-test")
        p._client = MagicMock()
        mock_choice = MagicMock()
        mock_choice.message.content = '{"classification": "green", "confidence": 0.9, "explanation": "win"}'
        mock_response = MagicMock()
        mock_response.choices = [mock_choice]
        p._client.chat.completions.create.return_value = mock_response
        r = p.classify("test prompt")
        assert r.classification == "green"
        assert r.confidence == 0.9
        assert not r.is_error


# --------------------------------------------------------------------------- #
#  Anthropic Provider
# --------------------------------------------------------------------------- #
class TestAnthropicProvider:
    def test_not_available_without_key(self):
        p = AnthropicProvider(api_key=None)
        assert not p.available()
        assert p.name() == "anthropic"

    def test_classify_without_key_returns_error(self):
        p = AnthropicProvider(api_key=None)
        r = p.classify("test")
        assert r.is_error
        assert "not configured" in r.error

    def test_parse_valid_json(self):
        p = AnthropicProvider(api_key="test")
        raw = '{"classification": "void", "confidence": 0.95, "explanation": "cancelled"}'
        r = p._parse(raw)
        assert r.classification == "void"
        assert r.confidence == 0.95
        assert not r.is_error

    def test_parse_invalid_json(self):
        p = AnthropicProvider(api_key="test")
        r = p._parse("not json")
        assert r.is_error

    def test_auth_error_handled(self):
        p = AnthropicProvider(api_key="bad-key")
        p._client = MagicMock()
        from anthropic import AuthenticationError
        mock_resp = MagicMock()
        mock_resp.status_code = 401
        p._client.messages.create.side_effect = AuthenticationError(
            message="bad key", response=mock_resp, body=None
        )
        r = p.classify("test")
        assert r.is_error
        assert "auth_error" in r.error

    def test_successful_mock_call(self):
        p = AnthropicProvider(api_key="test-key")
        p._client = MagicMock()
        mock_block = MagicMock()
        mock_block.text = '{"classification": "red", "confidence": 0.8, "explanation": "loss"}'
        mock_response = MagicMock()
        mock_response.content = [mock_block]
        p._client.messages.create.return_value = mock_response
        r = p.classify("test prompt")
        assert r.classification == "red"
        assert r.confidence == 0.8
        assert not r.is_error
        assert r.provider == "anthropic"


# --------------------------------------------------------------------------- #
#  AI Classifier
# --------------------------------------------------------------------------- #
class TestAIClassifierAdvanced:
    def test_budget_enforced(self):
        cfg = AuditConfig(llm_mode="assisted", max_llm_calls=1, openai_api_key="sk-test")
        mock_provider = MagicMock()
        mock_provider.available.return_value = True
        mock_provider.name.return_value = "mock"
        mock_provider.classify.return_value = LLMResponse(
            classification="green", confidence=0.9, explanation="ok", provider="mock"
        )
        cls = AIClassifier(cfg, [mock_provider])

        # First call works
        r1 = cls.classify({"descricao": "test"})
        assert r1.classification == "green"
        assert cls.budget_remaining == 0

        # Second call budget exhausted
        r2 = cls.classify({"descricao": "test2"})
        assert r2.is_error
        assert "budget_exhausted" in r2.error

    def test_all_providers_fail(self):
        cfg = AuditConfig(llm_mode="assisted", openai_api_key="sk-test")
        mock_provider = MagicMock()
        mock_provider.available.return_value = True
        mock_provider.name.return_value = "mock"
        mock_provider.classify.return_value = LLMResponse(
            classification="unknown", confidence=0.0, explanation="",
            provider="mock", error="some_error"
        )
        cls = AIClassifier(cfg, [mock_provider])
        r = cls.classify({"descricao": "test"})
        assert r.is_error
        assert "all_providers_failed" in r.error

    def test_dual_mode_picks_best(self):
        cfg = AuditConfig(llm_mode="assisted", llm_provider="dual",
                          openai_api_key="sk-test", anthropic_api_key="test")
        p1 = MagicMock()
        p1.available.return_value = True
        p1.name.return_value = "p1"
        p1.classify.return_value = LLMResponse(
            classification="green", confidence=0.7, explanation="ok", provider="p1"
        )
        p2 = MagicMock()
        p2.available.return_value = True
        p2.name.return_value = "p2"
        p2.classify.return_value = LLMResponse(
            classification="red", confidence=0.9, explanation="better", provider="p2"
        )
        cls = AIClassifier(cfg, [p1, p2])
        r = cls.classify({"descricao": "test"})
        assert r.classification == "red"  # p2 had higher confidence
        assert r.confidence == 0.9

    def test_should_classify_modes(self):
        # assisted: only unknowns
        cfg = AuditConfig(llm_mode="assisted", openai_api_key="sk-test")
        mock_p = MagicMock()
        mock_p.available.return_value = True
        cls = AIClassifier(cfg, [mock_p])
        assert cls.should_classify({"resultado_norm": "unknown"})
        assert not cls.should_classify({"resultado_norm": "green"})

        # review_all_suspects: unknowns + suspects
        cfg2 = AuditConfig(llm_mode="review_all_suspects", openai_api_key="sk-test")
        cls2 = AIClassifier(cfg2, [mock_p])
        assert cls2.should_classify({"resultado_norm": "unknown"})
        assert cls2.should_classify({"resultado_norm": "green", "is_suspect": True})
        assert not cls2.should_classify({"resultado_norm": "green", "is_suspect": False})

    def test_min_confidence_in_config(self):
        cfg = AuditConfig(min_confidence=0.8)
        assert cfg.min_confidence == 0.8


# --------------------------------------------------------------------------- #
#  Pipeline AI integration (end-to-end with mock)
# --------------------------------------------------------------------------- #
class TestPipelineAIIntegration:
    def test_ai_columns_present_without_ai(self):
        """Even without AI, columns should exist (empty)."""
        from bet_audit.cli import main as cli_main
        from pathlib import Path
        import tempfile
        with tempfile.TemporaryDirectory() as td:
            cli_main([
                "--input", str(Path("outputs/test_fixtures/test_edge_cases.xlsx").resolve()),
                "--output", td,
            ])
            import pandas as pd
            base = pd.read_csv(Path(td) / "base_completa.csv")
            for col in ["classificacao_ia", "confianca_ia", "explicacao_ia", "provider_ia", "modelo_ia"]:
                assert col in base.columns, f"Missing AI column: {col}"

    def test_ai_columns_present_with_ai_no_key(self):
        """With --use-ai but no key, should still have columns (empty)."""
        from bet_audit.cli import main as cli_main
        from pathlib import Path
        import tempfile
        with tempfile.TemporaryDirectory() as td:
            cli_main([
                "--input", str(Path("outputs/test_fixtures/test_edge_cases.xlsx").resolve()),
                "--output", td,
                "--use-ai",
            ])
            import pandas as pd
            base = pd.read_csv(Path(td) / "base_completa.csv")
            assert "classificacao_ia" in base.columns
            # All should be empty since no API key
            assert base["classificacao_ia"].fillna("").eq("").all()
