"""Tests for analisar_historico_apostas.py standalone script."""
from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import pandas as pd
import pytest

# Import functions from the standalone script
import sys

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from analisar_historico_apostas import (
    COLUMN_SYNONYMS,
    build_analysis,
    choose_sheet,
    export_outputs,
    first_matching_column,
    in_window,
    normalize_bookmakers,
    normalize_free_text,
    normalize_result_final,
    normalize_result_from_status,
    normalize_token,
    score_sheet,
    to_numeric,
)


# ---------------------------------------------------------------------------
# normalize_token
# ---------------------------------------------------------------------------
class TestNormalizeToken:
    def test_basic(self):
        assert normalize_token("  Hello World  ") == "hello_world"

    def test_accents(self):
        assert normalize_token("café") == "cafe"

    def test_none(self):
        assert normalize_token(None) == ""

    def test_special_chars(self):
        assert normalize_token("a@b#c") == "a_b_c"


# ---------------------------------------------------------------------------
# normalize_free_text
# ---------------------------------------------------------------------------
class TestNormalizeFreeText:
    def test_basic(self):
        assert normalize_free_text("Ganhou") == "ganhou"

    def test_accents(self):
        assert normalize_free_text("Anulação") == "anulacao"

    def test_none(self):
        assert normalize_free_text(None) == ""


# ---------------------------------------------------------------------------
# normalize_result_from_status
# ---------------------------------------------------------------------------
class TestNormalizeResultFromStatus:
    @pytest.mark.parametrize(
        "input_val,expected",
        [
            ("Ganha", "green"),
            ("Ganhou", "green"),
            ("Win", "green"),
            ("GREEN", "green"),
            ("Vitoria", "green"),
            ("Half Win", "green"),
            ("Meio Ganhou", "green"),
            ("Meia Ganha", "green"),
            ("Perdeu", "red"),
            ("Perdida", "red"),
            ("Loss", "red"),
            ("RED", "red"),
            ("Derrota", "red"),
            ("Half Loss", "red"),
            ("Meio Perdeu", "red"),
            ("Anulada", "void"),
            ("Empate", "void"),
            ("Void", "void"),
            ("Push", "void"),
            ("Cancel", "void"),
            ("Refund", "void"),
            ("Reembolso", "void"),
            ("", "unknown"),
            ("???", "unknown"),
            (None, "unknown"),
        ],
    )
    def test_classification(self, input_val, expected):
        assert normalize_result_from_status(input_val) == expected


# ---------------------------------------------------------------------------
# normalize_result_final
# ---------------------------------------------------------------------------
class TestNormalizeResultFinal:
    def test_status_takes_priority(self):
        assert normalize_result_final("Ganhou", -50) == "green"

    def test_fallback_positive_lucro(self):
        assert normalize_result_final("", 100) == "green"

    def test_fallback_negative_lucro(self):
        assert normalize_result_final("", -50) == "red"

    def test_fallback_zero_lucro(self):
        assert normalize_result_final("", 0) == "void"

    def test_fallback_nan_lucro(self):
        assert normalize_result_final("", np.nan) == "unknown"

    def test_none_status_positive(self):
        assert normalize_result_final(None, 100) == "green"


# ---------------------------------------------------------------------------
# to_numeric
# ---------------------------------------------------------------------------
class TestToNumeric:
    def test_already_numeric(self):
        s = pd.Series([1.0, 2.5, -3.0])
        result = to_numeric(s)
        pd.testing.assert_series_equal(result, s)

    def test_brazilian_format(self):
        s = pd.Series(["1.250,50"])
        assert to_numeric(s).iloc[0] == pytest.approx(1250.5)

    def test_currency_prefix(self):
        s = pd.Series(["R$ 500,00"])
        assert to_numeric(s).iloc[0] == pytest.approx(500.0)

    def test_empty_and_nan(self):
        s = pd.Series(["", "nan", "none"])
        result = to_numeric(s)
        assert result.isna().all()

    def test_comma_only(self):
        s = pd.Series(["1,5"])
        assert to_numeric(s).iloc[0] == pytest.approx(1.5)


# ---------------------------------------------------------------------------
# first_matching_column
# ---------------------------------------------------------------------------
class TestFirstMatchingColumn:
    def test_match(self):
        columns = ["Data", "Casa", "Lucro"]
        assert first_matching_column(columns, ["data", "date"]) == "Data"

    def test_no_match(self):
        columns = ["X", "Y"]
        assert first_matching_column(columns, ["data", "date"]) is None


# ---------------------------------------------------------------------------
# normalize_bookmakers
# ---------------------------------------------------------------------------
class TestNormalizeBookmakers:
    def test_case_normalization(self):
        s = pd.Series(["Bet365", "bet365", "BET365"])
        _, result = normalize_bookmakers(s)
        assert result.nunique() == 1

    def test_empty_becomes_desconhecida(self):
        s = pd.Series(["", None])
        _, result = normalize_bookmakers(s)
        assert (result == "desconhecida").all()


# ---------------------------------------------------------------------------
# in_window
# ---------------------------------------------------------------------------
class TestInWindow:
    def test_normal_window(self):
        hours = pd.Series([10.0, 14.0, 8.0])
        result = in_window(hours, 8.0, 12.0)
        assert result.tolist() == [True, False, True]

    def test_overnight_window(self):
        hours = pd.Series([23.0, 1.0, 12.0])
        result = in_window(hours, 22.0, 6.0)
        assert result.tolist() == [True, True, False]


# ---------------------------------------------------------------------------
# score_sheet
# ---------------------------------------------------------------------------
class TestScoreSheet:
    def test_good_sheet(self):
        df = pd.DataFrame({"Data": [1], "Casa": [2], "Lucro": [3], "Estado": [4]})
        sc = score_sheet(df, "test")
        assert sc.matched_groups >= 3

    def test_bad_sheet(self):
        df = pd.DataFrame({"X": [1], "Y": [2]})
        sc = score_sheet(df, "test")
        assert sc.matched_groups == 0


# ---------------------------------------------------------------------------
# build_analysis (integration)
# ---------------------------------------------------------------------------
class TestBuildAnalysis:
    def _make_df(self):
        return pd.DataFrame(
            {
                "Data": pd.to_datetime(
                    ["2026-01-15", "2026-01-16", "2026-01-17", "2026-02-01", "2026-02-02"]
                ),
                "Casa": ["Bet365", "Betano", "Bet365", "Pinnacle", "Bet365"],
                "Estado": ["Ganhou", "Perdeu", "Anulada", "Win", "Loss"],
                "Lucro": [100, -50, 0, 200, -75],
                "Aposta": ["game1", "game2", "game3", "game4", "game5"],
                "Odd": [2.0, 1.5, 1.8, 3.0, 1.9],
                "Stake": [1, 1, 1, 2, 1],
                "Valor": [50, 50, 50, 100, 50],
            }
        )

    def test_returns_expected_keys(self):
        result = build_analysis(self._make_df())
        expected_keys = {
            "base_tratada",
            "resumo",
            "dias_semana",
            "casas_geral",
            "casas_por_mes",
            "lideres_mes",
            "pivot_casas_mes",
            "top_20_red",
            "top_20_green",
            "faixas_horario",
        }
        assert set(result.keys()) == expected_keys

    def test_rows_count(self):
        result = build_analysis(self._make_df())
        assert len(result["base_tratada"]) == 5

    def test_missing_essential_column_raises(self):
        df = pd.DataFrame({"X": [1], "Y": [2], "Z": [3]})
        with pytest.raises(ValueError, match="Colunas essenciais ausentes"):
            build_analysis(df)

    def test_subtotal_rows_filtered(self):
        df = self._make_df()
        subtotal = pd.DataFrame(
            {
                "Data": [None],
                "Casa": ["Total"],
                "Estado": [""],
                "Lucro": [999],
                "Aposta": ["subtotal"],
                "Odd": [None],
                "Stake": [None],
                "Valor": [None],
            }
        )
        df_with_subtotal = pd.concat([df, subtotal], ignore_index=True)
        result = build_analysis(df_with_subtotal)
        assert len(result["base_tratada"]) == 5

    def test_inconsistency_count(self):
        df = pd.DataFrame(
            {
                "Data": pd.to_datetime(["2026-01-15", "2026-01-16"]),
                "Casa": ["Bet365", "Betano"],
                "Estado": ["Ganhou", "Perdeu"],
                "Lucro": [-50, 50],  # Both inconsistent
                "Aposta": ["a", "b"],
                "Odd": [2.0, 1.5],
                "Stake": [1, 1],
                "Valor": [50, 50],
            }
        )
        result = build_analysis(df)
        resumo = result["resumo"]
        incon_row = resumo[resumo["metrica"] == "inconsistencias_status_vs_lucro"]
        assert int(incon_row.iloc[0]["valor"]) == 2


# ---------------------------------------------------------------------------
# export_outputs (integration)
# ---------------------------------------------------------------------------
class TestExportOutputs:
    def test_creates_files(self, tmp_path):
        df = pd.DataFrame(
            {
                "Data": pd.to_datetime(["2026-01-15", "2026-01-16"]),
                "Casa": ["Bet365", "Betano"],
                "Estado": ["Ganhou", "Perdeu"],
                "Lucro": [100, -50],
                "Aposta": ["a", "b"],
                "Odd": [2.0, 1.5],
                "Stake": [1, 1],
                "Valor": [50, 50],
            }
        )
        analyses = build_analysis(df)
        result = export_outputs(
            output_dir=tmp_path,
            analyses=analyses,
            input_file=Path("test.xlsx"),
            sheet_name="Sheet1",
            sheet_reason="test",
            sheet_scores=[],
            resolved_columns={},
        )
        assert Path(result["excel_output"]).exists()
        assert Path(result["summary_json"]).exists()

        xls = pd.ExcelFile(result["excel_output"])
        assert len(xls.sheet_names) == 9

        summary = json.loads(Path(result["summary_json"]).read_text(encoding="utf-8"))
        assert summary["rows_base_tratada"] == 2
