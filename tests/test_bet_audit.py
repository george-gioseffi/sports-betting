"""Comprehensive tests for the bet_audit module."""
from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import pandas as pd
import pytest

# ---------------------------------------------------------------------------
# Config
# ---------------------------------------------------------------------------
from bet_audit.config import AuditConfig


class TestAuditConfig:
    def test_defaults(self):
        cfg = AuditConfig()
        assert cfg.search_provider == "off"
        assert cfg.llm_mode == "off"
        assert not cfg.llm_enabled
        assert not cfg.search_enabled

    def test_from_env_with_overrides(self):
        cfg = AuditConfig.from_env(search_provider="csv", llm_mode="assisted")
        assert cfg.search_provider == "csv"
        assert cfg.llm_mode == "assisted"
        assert cfg.llm_enabled
        assert cfg.search_enabled

    def test_has_api_key(self):
        cfg = AuditConfig(openai_api_key="sk-test")
        assert cfg.has_api_key("openai")
        assert not cfg.has_api_key("anthropic")

    def test_has_api_key_dual(self):
        cfg = AuditConfig(openai_api_key="sk-test")
        assert cfg.has_api_key("dual")


# ---------------------------------------------------------------------------
# Search Models
# ---------------------------------------------------------------------------
from bet_audit.search.models import ExternalResult, MatchResult


class TestExternalResult:
    def test_finished(self):
        r = ExternalResult(event_status="finished", home_score=2, away_score=1)
        assert r.finished
        assert r.score_known

    def test_cancelled(self):
        r = ExternalResult(event_status="cancelled")
        assert r.cancelled
        assert not r.finished

    def test_score_unknown(self):
        r = ExternalResult(event_status="finished", home_score=None, away_score=None)
        assert not r.score_known


# ---------------------------------------------------------------------------
# CSV Provider
# ---------------------------------------------------------------------------
from bet_audit.search.providers.csv_provider import CSVSearchProvider


@pytest.fixture
def csv_file(tmp_path: Path) -> Path:
    csv_path = tmp_path / "results.csv"
    csv_path.write_text(
        "sport,event_date,home_team,away_team,event_status,home_score,away_score\n"
        "futebol,2026-01-15,Flamengo,Palmeiras,finished,2,1\n"
        "futebol,2026-01-16,Barcelona,Real Madrid,finished,1,3\n"
        "futebol,2026-02-01,Man City,Liverpool,cancelled,,\n",
        encoding="utf-8",
    )
    return csv_path


class TestCSVProvider:
    def test_load_and_search(self, csv_file: Path):
        provider = CSVSearchProvider(csv_file)
        results = provider.search("Flamengo x Palmeiras")
        assert len(results) >= 1
        assert results[0].home_team == "Flamengo"

    def test_search_with_date(self, csv_file: Path):
        provider = CSVSearchProvider(csv_file)
        results = provider.search("Flamengo", event_date="2026-01-15")
        assert len(results) >= 1

    def test_search_no_match(self, csv_file: Path):
        provider = CSVSearchProvider(csv_file)
        results = provider.search("TimeTotalmenteDesconhecido")
        assert len(results) == 0

    def test_empty_query(self, csv_file: Path):
        provider = CSVSearchProvider(csv_file)
        assert provider.search("") == []

    def test_file_not_found(self, tmp_path: Path):
        with pytest.raises(FileNotFoundError):
            CSVSearchProvider(tmp_path / "nonexistent.csv")

    def test_cancelled_score_none(self, csv_file: Path):
        provider = CSVSearchProvider(csv_file)
        results = provider.search("Man City", event_date="2026-02-01")
        assert len(results) >= 1
        assert results[0].home_score is None


# ---------------------------------------------------------------------------
# Mock Provider
# ---------------------------------------------------------------------------
from bet_audit.search.providers.mock_provider import MockSearchProvider


class TestMockProvider:
    def test_search_hit(self):
        provider = MockSearchProvider()
        results = provider.search("Flamengo x Palmeiras", event_date="2026-01-15")
        assert len(results) >= 1

    def test_search_miss(self):
        provider = MockSearchProvider()
        results = provider.search("TimeInexistente")
        assert len(results) == 0


# ---------------------------------------------------------------------------
# Matcher
# ---------------------------------------------------------------------------
from bet_audit.search.matcher import match_bet_to_external


class TestMatcher:
    def test_finds_match(self, csv_file: Path):
        provider = CSVSearchProvider(csv_file)
        result = match_bet_to_external("Flamengo x Palmeiras - Moneyline Home", "2026-01-15", provider)
        assert result.found
        assert result.confidence >= 0.5
        assert result.external is not None
        assert result.external.home_team == "Flamengo"

    def test_no_match(self, csv_file: Path):
        provider = CSVSearchProvider(csv_file)
        result = match_bet_to_external("TimeX x TimeY", "2026-01-15", provider)
        assert not result.found

    def test_empty_description(self, csv_file: Path):
        provider = CSVSearchProvider(csv_file)
        result = match_bet_to_external("", None, provider)
        assert not result.found
        assert result.match_reason == "descricao vazia"


# ---------------------------------------------------------------------------
# Resolver (market detection + outcome resolution)
# ---------------------------------------------------------------------------
from bet_audit.search.resolver import detect_market, resolve_outcome


class TestDetectMarket:
    @pytest.mark.parametrize(
        "desc,expected",
        [
            ("Flamengo x Palmeiras - Moneyline Home", "moneyline_home"),
            ("Over 2.5", "over"),
            ("Under 1.5 gols", "under"),
            ("BTTS - Sim", "btts_yes"),
            ("BTTS - Nao", "btts_no"),
            ("DNB Home", "dnb_home"),
            ("Apenas nome de time", "unknown"),
        ],
    )
    def test_detection(self, desc, expected):
        assert detect_market(desc) == expected


class TestResolveOutcome:
    def test_moneyline_home_win(self):
        ext = ExternalResult(event_status="finished", home_score=2, away_score=1)
        result, reason, conf = resolve_outcome("Moneyline Home", ext)
        assert result == "green"
        assert conf >= 0.9

    def test_moneyline_home_loss(self):
        ext = ExternalResult(event_status="finished", home_score=0, away_score=2)
        result, _, _ = resolve_outcome("Moneyline Home", ext)
        assert result == "red"

    def test_over(self):
        ext = ExternalResult(event_status="finished", home_score=2, away_score=2)
        result, _, _ = resolve_outcome("Over 2.5", ext)
        assert result == "green"  # 4 > 2.5

    def test_under(self):
        ext = ExternalResult(event_status="finished", home_score=0, away_score=1)
        result, _, _ = resolve_outcome("Under 2.5", ext)
        assert result == "green"  # 1 < 2.5

    def test_btts_yes(self):
        ext = ExternalResult(event_status="finished", home_score=1, away_score=1)
        result, _, _ = resolve_outcome("BTTS Sim", ext)
        assert result == "green"

    def test_btts_no(self):
        ext = ExternalResult(event_status="finished", home_score=1, away_score=0)
        result, _, _ = resolve_outcome("BTTS Nao", ext)
        assert result == "green"

    def test_cancelled(self):
        ext = ExternalResult(event_status="cancelled")
        result, _, conf = resolve_outcome("Anything", ext)
        assert result == "void"
        assert conf >= 0.9

    def test_unknown_market(self):
        ext = ExternalResult(event_status="finished", home_score=1, away_score=0)
        result, reason, _ = resolve_outcome("Apenas nome time", ext)
        assert result == "unknown"
        assert "nao suportado" in reason

    def test_dnb_draw_void(self):
        ext = ExternalResult(event_status="finished", home_score=1, away_score=1)
        result, _, _ = resolve_outcome("DNB Home", ext)
        assert result == "void"


# ---------------------------------------------------------------------------
# AI (no-API fallback)
# ---------------------------------------------------------------------------
from bet_audit.ai.base_llm import LLMResponse
from bet_audit.ai.classifier import AIClassifier
from bet_audit.ai.openai_provider import OpenAIProvider
from bet_audit.ai.anthropic_provider import AnthropicProvider


class TestLLMProviders:
    def test_openai_not_available_without_key(self):
        p = OpenAIProvider(api_key=None)
        assert not p.available()
        result = p.classify("test")
        assert result.is_error
        assert result.classification == "unknown"

    def test_anthropic_not_available_without_key(self):
        p = AnthropicProvider(api_key=None)
        assert not p.available()
        result = p.classify("test")
        assert result.is_error

    def test_classifier_budget(self):
        cfg = AuditConfig(llm_mode="assisted", max_llm_calls=2)
        classifier = AIClassifier(cfg, [])
        assert classifier.budget_remaining == 2
        assert not classifier.available()  # no providers

    def test_classifier_off(self):
        cfg = AuditConfig(llm_mode="off")
        classifier = AIClassifier(cfg, [])
        result = classifier.classify({"descricao": "test"})
        assert result.classification == "unknown"
        assert "off" in result.explanation.lower()

    def test_should_classify_off(self):
        cfg = AuditConfig(llm_mode="off")
        classifier = AIClassifier(cfg, [])
        assert not classifier.should_classify({"resultado_norm": "unknown"})


# ---------------------------------------------------------------------------
# Desplanilhadas
# ---------------------------------------------------------------------------
from bet_audit.consolidation.desplanilhadas import detect_desplanilhadas, classify_desplanilhada_reason


class TestDesplanilhadas:
    def test_empty_status_and_lucro(self):
        df = pd.DataFrame({
            "status_original": [""],
            "lucro": [np.nan],
            "descricao": ["Jogo X"],
            "resultado_texto": ["unknown"],
            "odd": [2.0],
            "stake": [1.0],
        })
        assert detect_desplanilhadas(df).iloc[0]

    def test_status_green_lucro_negative(self):
        df = pd.DataFrame({
            "status_original": ["Ganhou"],
            "lucro": [-100.0],
            "descricao": ["Jogo X"],
            "resultado_texto": ["green"],
        })
        assert detect_desplanilhadas(df).iloc[0]

    def test_status_red_lucro_positive(self):
        df = pd.DataFrame({
            "status_original": ["Perdeu"],
            "lucro": [100.0],
            "descricao": ["Jogo X"],
            "resultado_texto": ["red"],
        })
        assert detect_desplanilhadas(df).iloc[0]

    def test_normal_row_not_flagged(self):
        df = pd.DataFrame({
            "status_original": ["Ganhou"],
            "lucro": [100.0],
            "descricao": ["Jogo X"],
            "resultado_texto": ["green"],
        })
        assert not detect_desplanilhadas(df).iloc[0]

    def test_classify_reason(self):
        row = pd.Series({
            "status_original": "Ganhou",
            "lucro": -50.0,
            "descricao": "Jogo X",
            "resultado_texto": "green",
        })
        reason = classify_desplanilhada_reason(row)
        assert "green" in reason and "lucro" in reason


# ---------------------------------------------------------------------------
# Consolidator
# ---------------------------------------------------------------------------
from bet_audit.consolidation.consolidator import consolidate


class TestConsolidator:
    def _base_df(self):
        return pd.DataFrame({
            "status_original": ["Ganhou", "Perdeu", "Anulada", "Ganhou", "", ""],
            "lucro": [100, -50, 0, -30, 200, np.nan],
            "descricao": ["a", "b", "c", "d", "e", "f"],
            "resultado_texto": ["green", "red", "void", "green", "unknown", "unknown"],
            "resultado_norm": ["green", "red", "void", "green", "green", "unknown"],
            "resultado_externo": ["", "", "", "", "green", ""],
            "confianca_externo": [0, 0, 0, 0, 0.95, 0],
            "motivo_externo": ["", "", "", "", "mandante venceu 2x1", ""],
        })

    def test_adds_columns(self):
        df = consolidate(self._base_df())
        assert "veredito_final" in df.columns
        assert "fonte_veredito_final" in df.columns
        assert "confidence_final" in df.columns
        assert "is_desplanilhada" in df.columns

    def test_normal_green_kept(self):
        df = consolidate(self._base_df())
        assert df.iloc[0]["veredito_final"] == "MANTER_GREEN"
        assert df.iloc[0]["fonte_veredito_final"] == "regra"

    def test_normal_red_kept(self):
        df = consolidate(self._base_df())
        assert df.iloc[1]["veredito_final"] == "MANTER_RED"

    def test_desplanilhada_detected(self):
        df = consolidate(self._base_df())
        # Row 3: status="Ganhou" but lucro=-30 -> desplanilhada
        assert df.iloc[3]["is_desplanilhada"]
        assert df.iloc[3]["veredito_final"] == "DESPLANILHADA"

    def test_external_overrides_rule(self):
        df = consolidate(self._base_df())
        # Row 4: resultado_norm=green (from lucro), externo also green with conf=0.95
        assert df.iloc[4]["fonte_veredito_final"] == "externo"

    def test_unknown_goes_to_review(self):
        df = consolidate(self._base_df())
        # Row 5: unknown everything -> desplanilhada (status empty, lucro nan)
        assert df.iloc[5]["is_desplanilhada"]

    def test_priority_order(self):
        """External > Rule > AI > Manual"""
        df = pd.DataFrame({
            "status_original": ["Perdeu"],
            "lucro": [-50],
            "descricao": ["test"],
            "resultado_texto": ["red"],
            "resultado_norm": ["red"],
            "resultado_externo": ["green"],
            "confianca_externo": [0.95],
            "motivo_externo": ["mandante venceu"],
            "classificacao_ia": ["red"],
            "confianca_ia": [0.8],
        })
        result = consolidate(df)
        # External says green, rule says red, AI says red -> external wins
        assert result.iloc[0]["veredito_final"] == "CORRIGIR_PARA_GREEN"
        assert result.iloc[0]["fonte_veredito_final"] == "externo"


# ---------------------------------------------------------------------------
# Export
# ---------------------------------------------------------------------------
from bet_audit.export.exporter import export_audit


class TestExporter:
    def test_creates_files(self, tmp_path: Path):
        df = pd.DataFrame({
            "data_hora": pd.to_datetime(["2026-01-15"]),
            "descricao": ["test"],
            "veredito_final": ["MANTER_GREEN"],
            "fonte_veredito_final": ["regra"],
            "motivo_veredito_final": ["ok"],
            "confidence_final": [0.85],
            "prioridade_revisao": [0],
            "is_desplanilhada": [False],
            "resultado_externo": [""],
        })
        result = export_audit(df, tmp_path, {"test": True})
        assert Path(result["excel_output"]).exists()
        assert Path(result["summary_json"]).exists()

        xls = pd.ExcelFile(result["excel_output"])
        expected = ["resumo", "suspeitas", "desplanilhadas", "revisao_manual",
                    "corrigir_green_red", "sem_match_externo", "auditadas_com_ia", "base_completa"]
        for tab in expected:
            assert tab in xls.sheet_names, f"Missing tab: {tab}"


# ---------------------------------------------------------------------------
# Pipeline integration (CLI end-to-end)
# ---------------------------------------------------------------------------
from bet_audit.cli import main as cli_main


class TestCLIEndToEnd:
    @pytest.fixture
    def edge_xlsx(self) -> str:
        return str(Path("outputs/test_fixtures/test_edge_cases.xlsx").resolve())

    @pytest.fixture
    def ext_csv(self) -> str:
        return str(Path("outputs/test_fixtures/external_results.csv").resolve())

    def test_no_search_no_ai(self, edge_xlsx: str, tmp_path: Path):
        cli_main(["--input", edge_xlsx, "--output", str(tmp_path)])
        xlsx_files = list(tmp_path.glob("*.xlsx"))
        assert len(xlsx_files) == 1
        json_files = list(tmp_path.glob("*.json"))
        assert len(json_files) == 1

    def test_csv_search(self, edge_xlsx: str, ext_csv: str, tmp_path: Path):
        cli_main([
            "--input", edge_xlsx,
            "--output", str(tmp_path),
            "--search-provider", "csv",
            "--search-data-file", ext_csv,
        ])
        base = pd.read_csv(tmp_path / "base_completa.csv")
        assert "veredito_final" in base.columns
        assert "resultado_externo" in base.columns
        matched = base["evento_match"].fillna("").astype(str).str.len().gt(0).sum()
        assert matched > 0

    def test_mock_search(self, edge_xlsx: str, tmp_path: Path):
        cli_main([
            "--input", edge_xlsx,
            "--output", str(tmp_path),
            "--search-provider", "mock",
        ])
        assert list(tmp_path.glob("*.xlsx"))

    def test_date_filter(self, edge_xlsx: str, tmp_path: Path):
        cli_main([
            "--input", edge_xlsx,
            "--output", str(tmp_path),
            "--date-from", "2026-02-01",
            "--date-to", "2026-02-28",
        ])
        base = pd.read_csv(tmp_path / "base_completa.csv")
        assert len(base) < 17  # original has 17 rows

    def test_only_issues(self, edge_xlsx: str, ext_csv: str, tmp_path: Path):
        cli_main([
            "--input", edge_xlsx,
            "--output", str(tmp_path),
            "--search-provider", "csv",
            "--search-data-file", ext_csv,
            "--only-issues",
        ])
        base = pd.read_csv(tmp_path / "base_completa.csv")
        # Only issues exported
        assert all(
            v in ("REVISAO_MANUAL", "DESPLANILHADA", "CORRIGIR_PARA_GREEN", "CORRIGIR_PARA_RED", "CORRIGIR_PARA_ANULADA")
            for v in base["veredito_final"]
        )

    def test_use_ai_no_key(self, edge_xlsx: str, tmp_path: Path):
        cli_main(["--input", edge_xlsx, "--output", str(tmp_path), "--use-ai"])
        base = pd.read_csv(tmp_path / "base_completa.csv")
        # Should complete without error; AI columns should exist but be empty
        assert "classificacao_ia" in base.columns

    def test_missing_file(self, tmp_path: Path):
        with pytest.raises(FileNotFoundError):
            cli_main(["--input", str(tmp_path / "nope.xlsx"), "--output", str(tmp_path)])

    def test_missing_column(self, tmp_path: Path):
        bad_xlsx = tmp_path / "bad.xlsx"
        pd.DataFrame({"X": [1], "Y": [2]}).to_excel(bad_xlsx, index=False)
        with pytest.raises(ValueError, match="Colunas essenciais"):
            cli_main(["--input", str(bad_xlsx), "--output", str(tmp_path / "out")])
