from __future__ import annotations

from dataclasses import dataclass
from datetime import date

import pandas as pd
import streamlit as st

from app.translations import LANG_OPTIONS, t, to_market_label


@dataclass(frozen=True)
class GlobalFilters:
    strategies: list[str]
    leagues: list[str]
    markets: list[str]
    methods: list[str]
    start_date: date | None
    end_date: date | None
    lang: str


def _extract_date_range(load_mart_fn) -> tuple[date | None, date | None]:
    bankroll_df = load_mart_fn("fact_bankroll_evolution")
    if bankroll_df.empty or "settled_date" not in bankroll_df.columns:
        return None, None
    series = pd.to_datetime(bankroll_df["settled_date"], errors="coerce").dropna()
    if series.empty:
        return None, None
    return series.min().date(), series.max().date()


def _options(df: pd.DataFrame, column: str) -> list[str]:
    if column not in df.columns:
        return []
    return sorted(df[column].dropna().astype(str).unique().tolist())


def build_global_filters(load_mart_fn) -> GlobalFilters:
    strategy_df = load_mart_fn("mart_strategy_performance")
    league_df = load_mart_fn("mart_league_performance")
    market_df = load_mart_fn("mart_market_performance")
    scenario_df = load_mart_fn("mart_bankroll_scenarios_summary")
    min_date, max_date = _extract_date_range(load_mart_fn)

    language_label = st.sidebar.selectbox(
        "Language / Idioma",
        options=list(LANG_OPTIONS.keys()),
        key="global_language",
    )
    lang = LANG_OPTIONS.get(language_label, "en")

    strategy_options = _options(strategy_df, "strategy")
    league_options = _options(league_df, "league")
    market_options = _options(market_df, "market")
    method_options = _options(scenario_df, "method")
    market_label_to_code = {to_market_label(code, lang): code for code in market_options}
    market_label_options = list(market_label_to_code.keys())

    st.sidebar.markdown(t("sidebar_filters", lang))
    strategies = st.sidebar.multiselect(
        t("filter_strategies", lang),
        options=strategy_options,
        default=strategy_options,
        key="global_strategies",
    )
    leagues = st.sidebar.multiselect(
        t("filter_leagues", lang),
        options=league_options,
        default=league_options,
        key="global_leagues",
    )
    selected_market_labels = st.sidebar.multiselect(
        t("filter_markets", lang),
        options=market_label_options,
        default=market_label_options,
        key="global_markets",
    )
    markets = [market_label_to_code[label] for label in selected_market_labels]
    methods = st.sidebar.multiselect(
        t("filter_methods", lang),
        options=method_options,
        default=method_options,
        key="global_methods",
    )

    if min_date and max_date:
        date_range = st.sidebar.date_input(
            t("filter_date_range", lang),
            value=(min_date, max_date),
            min_value=min_date,
            max_value=max_date,
            key="global_date_range",
        )
        if isinstance(date_range, tuple) and len(date_range) == 2:
            start_date, end_date = date_range
        else:
            start_date, end_date = min_date, max_date
    else:
        start_date, end_date = None, None

    st.sidebar.caption(t("filter_caption", lang))
    return GlobalFilters(
        strategies=strategies,
        leagues=leagues,
        markets=markets,
        methods=methods,
        start_date=start_date,
        end_date=end_date,
        lang=lang,
    )


def _filter_by_date(df: pd.DataFrame, filters: GlobalFilters) -> pd.DataFrame:
    if filters.start_date is None or filters.end_date is None:
        return df

    if "month" in df.columns:
        out = df.copy()
        month_dates = pd.to_datetime(out["month"].astype(str) + "-01", errors="coerce").dt.date
        mask = (month_dates >= filters.start_date) & (month_dates <= filters.end_date)
        return out.loc[mask].reset_index(drop=True)

    date_cols = ["settled_date", "placed_date", "date", "placed_ts", "snapshot_ts"]
    for col in date_cols:
        if col in df.columns:
            out = df.copy()
            parsed = pd.to_datetime(out[col], errors="coerce").dt.date
            mask = (parsed >= filters.start_date) & (parsed <= filters.end_date)
            return out.loc[mask].reset_index(drop=True)
    return df


def apply_global_filters(df: pd.DataFrame, filters: GlobalFilters) -> pd.DataFrame:
    if df.empty:
        return df
    out = df.copy()
    if "strategy" in out.columns and filters.strategies:
        out = out[out["strategy"].astype(str).isin(filters.strategies)]
    if "league" in out.columns and filters.leagues:
        out = out[out["league"].astype(str).isin(filters.leagues)]
    if "market" in out.columns and filters.markets:
        out = out[out["market"].astype(str).isin(filters.markets)]
    if "method" in out.columns and filters.methods:
        out = out[out["method"].astype(str).isin(filters.methods)]
    out = _filter_by_date(out, filters)
    return out.reset_index(drop=True)


def apply_market_labels(df: pd.DataFrame, lang: str = "en", column: str = "market") -> pd.DataFrame:
    if df.empty or column not in df.columns:
        return df
    out = df.copy()
    out[column] = out[column].map(lambda value: to_market_label(str(value), lang))
    return out
