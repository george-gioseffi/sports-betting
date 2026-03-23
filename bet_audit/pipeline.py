"""Main audit pipeline — orchestrates search, rules, AI, and consolidation."""
from __future__ import annotations

import logging
from pathlib import Path

import numpy as np
import pandas as pd

from bet_audit.ai.anthropic_provider import AnthropicProvider
from bet_audit.ai.classifier import AIClassifier
from bet_audit.ai.openai_provider import OpenAIProvider
from bet_audit.config import AuditConfig
from bet_audit.consolidation.consolidator import consolidate
from bet_audit.export.exporter import export_audit
from bet_audit.search.base import BaseSearchProvider
from bet_audit.search.matcher import match_bet_to_external
from bet_audit.search.providers.csv_provider import CSVSearchProvider
from bet_audit.search.providers.mock_provider import MockSearchProvider
from bet_audit.search.resolver import detect_market, resolve_outcome

# Re-use normalisation helpers from the existing analysis script
from analisar_historico_apostas import (
    COLUMN_SYNONYMS,
    choose_sheet,
    first_matching_column,
    normalize_bookmakers,
    normalize_result_final,
    normalize_result_from_status,
    to_numeric,
)

logger = logging.getLogger(__name__)


def _build_search_provider(config: AuditConfig) -> BaseSearchProvider | None:
    if config.search_provider == "csv":
        if not config.search_data_file:
            logger.warning("search_provider=csv but no search_data_file set; skipping search")
            return None
        return CSVSearchProvider(config.search_data_file)
    if config.search_provider == "mock":
        return MockSearchProvider()
    return None


def _build_ai_classifier(config: AuditConfig) -> AIClassifier:
    providers = []
    if config.llm_provider in ("openai", "dual"):
        providers.append(OpenAIProvider(api_key=config.openai_api_key))
    if config.llm_provider in ("anthropic", "dual"):
        providers.append(AnthropicProvider(api_key=config.anthropic_api_key))
    return AIClassifier(config, providers)


def load_and_normalise(config: AuditConfig) -> tuple[pd.DataFrame, dict, str, str]:
    """Load Excel, choose sheet, normalise columns. Returns (df, resolved_cols, sheet_name, reason)."""
    input_path = Path(config.input_file).expanduser().resolve()
    if not input_path.exists():
        raise FileNotFoundError(f"Arquivo nao encontrado: {input_path}")

    if config.sheet_name:
        sheet_name = config.sheet_name
        reason = f"Aba '{sheet_name}' especificada via CLI"
        sheet_scores = []
    else:
        sheet_name, sheet_scores, reason = choose_sheet(input_path)

    raw_df = pd.read_excel(input_path, sheet_name=sheet_name)
    original_cols = list(raw_df.columns)

    resolved = {
        logical: first_matching_column(original_cols, candidates)
        for logical, candidates in COLUMN_SYNONYMS.items()
    }

    missing = [k for k in ["data_hora", "casa", "lucro"] if resolved.get(k) is None]
    if missing:
        raise ValueError(f"Colunas essenciais ausentes: {missing}")

    # Build normalised base
    base = pd.DataFrame()
    base["data_hora"] = pd.to_datetime(
        raw_df[resolved["data_hora"]], errors="coerce", dayfirst=True, format="mixed"
    )
    base["casa_original"] = raw_df[resolved["casa"]].astype(str)
    base["lucro"] = to_numeric(raw_df[resolved["lucro"]])
    base["status_original"] = (
        raw_df[resolved["status"]].astype(str) if resolved["status"] else pd.Series("", index=raw_df.index)
    )
    base["descricao"] = (
        raw_df[resolved["descricao"]].astype(str) if resolved["descricao"] else pd.Series("", index=raw_df.index)
    )
    base["odd"] = to_numeric(raw_df[resolved["odd"]]) if resolved["odd"] else np.nan
    base["stake"] = to_numeric(raw_df[resolved["stake"]]) if resolved["stake"] else np.nan
    base["valor_apostado"] = (
        to_numeric(raw_df[resolved["valor_apostado"]]) if resolved["valor_apostado"] else np.nan
    )

    # Combine date + time if needed
    if resolved["horario"]:
        time_s = pd.to_datetime(raw_df[resolved["horario"]].astype(str), errors="coerce")
        if base["data_hora"].dt.hour.fillna(0).eq(0).all() and time_s.notna().any():
            base["data_hora"] = (
                base["data_hora"].dt.normalize()
                + pd.to_timedelta(time_s.dt.hour.fillna(0), unit="h")
                + pd.to_timedelta(time_s.dt.minute.fillna(0), unit="m")
            )

    # Clean strings
    base["casa_original"] = base["casa_original"].fillna("").str.strip().str.replace(r"\s+", " ", regex=True)
    base["status_original"] = base["status_original"].fillna("").str.strip()
    base["descricao"] = base["descricao"].fillna("").str.strip()

    # Filter subtotals and rows missing essential data
    combo = (
        base["casa_original"].str.lower() + " " + base["status_original"].str.lower()
        + " " + base["descricao"].str.lower()
    )
    subtotal_mask = combo.str.contains(r"\btotal\b|\bsubtotal\b", na=False) & base["data_hora"].isna()
    base = base.loc[~subtotal_mask].copy()
    base = base.dropna(subset=["data_hora", "lucro"])

    # Normalise bookmakers
    _, base["casa"] = normalize_bookmakers(base["casa_original"])

    # Deterministic result classification
    base["resultado_texto"] = base["status_original"].map(normalize_result_from_status)
    base["resultado_norm"] = [
        normalize_result_final(s, l)
        for s, l in zip(base["status_original"], base["lucro"], strict=False)
    ]

    base["is_green"] = base["resultado_norm"].eq("green")
    base["is_red"] = base["resultado_norm"].eq("red")
    base["is_void"] = base["resultado_norm"].eq("void")

    base["data"] = base["data_hora"].dt.date.astype(str)
    base["horario"] = base["data_hora"].dt.strftime("%H:%M:%S")
    base["mes"] = base["data_hora"].dt.to_period("M").astype(str)

    # Date filters
    if config.date_from:
        base = base[base["data"] >= config.date_from].copy()
    if config.date_to:
        base = base[base["data"] <= config.date_to].copy()

    return base, resolved, sheet_name, reason


def run_search_phase(df: pd.DataFrame, provider: BaseSearchProvider | None) -> pd.DataFrame:
    """Phase 1: match bets to external results and resolve outcomes."""
    out = df.copy()
    out["evento_match"] = ""
    out["resultado_externo"] = ""
    out["confianca_externo"] = 0.0
    out["motivo_externo"] = ""
    out["mercado_detectado"] = ""

    if provider is None:
        logger.info("Search provider disabled; skipping search phase.")
        return out

    logger.info("Running search phase with provider: %s", provider.name())
    matched = 0
    for idx in out.index:
        desc = str(out.at[idx, "descricao"])
        date = str(out.at[idx, "data"])
        if not desc.strip():
            continue

        result = match_bet_to_external(desc, date, provider)
        out.at[idx, "mercado_detectado"] = detect_market(desc)

        if result.found and result.external is not None:
            matched += 1
            ext = result.external
            out.at[idx, "evento_match"] = f"{ext.home_team} x {ext.away_team} ({ext.event_date})"

            outcome, reason, conf = resolve_outcome(desc, ext)
            out.at[idx, "resultado_externo"] = outcome
            out.at[idx, "confianca_externo"] = conf
            out.at[idx, "motivo_externo"] = reason

    logger.info("Search phase: %d/%d bets matched to external results.", matched, len(out))
    return out


def run_ai_phase(df: pd.DataFrame, classifier: AIClassifier) -> pd.DataFrame:
    """Phase 2: AI classification for ambiguous bets."""
    out = df.copy()
    out["classificacao_ia"] = ""
    out["confianca_ia"] = 0.0
    out["explicacao_ia"] = ""
    out["provider_ia"] = ""
    out["modelo_ia"] = ""

    if not classifier.available():
        logger.info("AI classifier not available; skipping AI phase.")
        return out

    # Mark suspects
    out["is_suspect"] = (
        (out["resultado_norm"] == "unknown")
        | ((out["resultado_texto"] == "green") & (out["lucro"] <= 0))
        | ((out["resultado_texto"] == "red") & (out["lucro"] >= 0))
    )

    classified = 0
    for idx in out.index:
        row = out.loc[idx].to_dict()
        if not classifier.should_classify(row):
            continue

        response = classifier.classify(row)
        out.at[idx, "classificacao_ia"] = response.classification
        out.at[idx, "confianca_ia"] = response.confidence
        out.at[idx, "explicacao_ia"] = response.explanation
        out.at[idx, "provider_ia"] = response.provider
        out.at[idx, "modelo_ia"] = response.model
        classified += 1

    logger.info("AI phase: %d bets classified (budget remaining: %d).", classified, classifier.budget_remaining)
    return out


def run_audit(config: AuditConfig) -> dict[str, str]:
    """Execute the full audit pipeline."""
    logging.basicConfig(
        level=logging.DEBUG if config.verbose else logging.INFO,
        format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )

    # 1. Load and normalise
    logger.info("Loading input: %s", config.input_file)
    df, resolved_cols, sheet_name, sheet_reason = load_and_normalise(config)
    logger.info("Loaded %d rows from sheet '%s'", len(df), sheet_name)

    # 2. Search phase (rules run first via resultado_norm, then search enriches)
    provider = _build_search_provider(config)
    df = run_search_phase(df, provider)

    # 3. AI phase
    classifier = _build_ai_classifier(config)
    df = run_ai_phase(df, classifier)

    # 4. Consolidation
    df = consolidate(df)

    # 5. Filter only issues if requested
    if config.only_issues:
        issue_verdicts = ["REVISAO_MANUAL", "DESPLANILHADA", "CORRIGIR_PARA_GREEN", "CORRIGIR_PARA_RED", "CORRIGIR_PARA_ANULADA"]
        df = df[df["veredito_final"].isin(issue_verdicts)].copy()

    # 6. Export
    output_dir = Path(config.output_dir).expanduser().resolve()
    metadata = {
        "input_file": config.input_file,
        "chosen_sheet": sheet_name,
        "sheet_reason": sheet_reason,
        "resolved_columns": resolved_cols,
        "search_provider": provider.name() if provider else "off",
        "llm_mode": config.llm_mode,
        "llm_provider": config.llm_provider,
        "ai_calls_made": classifier.calls_made,
        "date_from": config.date_from,
        "date_to": config.date_to,
        "only_issues": config.only_issues,
        "rows_processed": len(df),
    }

    outputs = export_audit(df, output_dir, metadata)
    logger.info("Audit complete. Output: %s", outputs["output_dir"])
    return outputs
