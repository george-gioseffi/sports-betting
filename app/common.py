from __future__ import annotations

from dataclasses import dataclass
from datetime import date
from pathlib import Path

import pandas as pd
import plotly.graph_objects as go
import streamlit as st

BASE_DIR = Path(__file__).resolve().parents[1]
MARTS_DIR = BASE_DIR / "data" / "marts"
MARKET_LABELS = {
    "MONEYLINE_HOME": "Home Win",
    "OVER_2_5": "Over 2.5",
    "BTTS_YES": "BTTS Yes",
    "DNB_HOME": "Home DNB",
}
ALERT_LABELS = {
    "drawdown_limit_breach": "Drawdown Limit Breach",
    "elevated_volatility": "Elevated Volatility",
    "league_concentration": "League Concentration",
    "long_loss_streak": "Long Loss Streak",
    "no_critical_alerts": "No Critical Alerts",
}
SEVERITY_ORDER = {"high": 0, "medium": 1, "info": 2}


@st.cache_data(show_spinner=False)
def load_mart(table_name: str) -> pd.DataFrame:
    path = MARTS_DIR / f"{table_name}.csv"
    if not path.exists():
        return pd.DataFrame()
    return pd.read_csv(path)


def format_pct(value: float) -> str:
    return f"{value * 100:.2f}%"


def show_missing_data_message() -> None:
    st.warning(
        "Marts not found. Run `python -m src.main seed` and `python -m src.main pipeline` first."
    )


@dataclass(frozen=True)
class GlobalFilters:
    strategies: list[str]
    leagues: list[str]
    markets: list[str]
    methods: list[str]
    start_date: date | None
    end_date: date | None


def inject_styles() -> None:
    st.markdown(
        """
<style>
.block-container {
    padding-top: 1.2rem;
    padding-bottom: 2rem;
}
.hero-title {
    font-size: 2rem;
    font-weight: 700;
    margin-bottom: 0.2rem;
}
.hero-subtitle {
    color: #4b5563;
    margin-bottom: 1rem;
}
.section-note {
    color: #6b7280;
    font-size: 0.92rem;
    margin-top: -0.2rem;
    margin-bottom: 0.8rem;
}
[data-testid="stMetricValue"] {
    font-size: 1.45rem;
}
</style>
""",
        unsafe_allow_html=True,
    )


def render_page_header(title: str, subtitle: str) -> None:
    st.markdown(f"<div class='hero-title'>{title}</div>", unsafe_allow_html=True)
    st.markdown(f"<div class='hero-subtitle'>{subtitle}</div>", unsafe_allow_html=True)


def render_section_note(note: str) -> None:
    st.markdown(f"<div class='section-note'>{note}</div>", unsafe_allow_html=True)


def apply_chart_style(fig: go.Figure) -> go.Figure:
    fig.update_layout(
        template="plotly_white",
        margin=dict(l=16, r=16, t=56, b=12),
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="left", x=0),
    )
    fig.update_xaxes(showgrid=False)
    fig.update_yaxes(showgrid=True, gridcolor="#e5e7eb")
    return fig


def render_kpi_strip(overall_df: pd.DataFrame) -> None:
    if overall_df.empty:
        return
    row = overall_df.iloc[0]
    c1, c2, c3, c4, c5, c6 = st.columns(6)
    c1.metric("Total Bets", f"{int(row['total_bets'])}")
    c2.metric("Win Rate", format_pct(float(row["win_rate"])))
    c3.metric("Yield", format_pct(float(row["yield_pct"])))
    c4.metric("ROI", format_pct(float(row["roi"])))
    c5.metric("Avg CLV", format_pct(float(row["avg_clv"])))
    c6.metric("Max Drawdown", format_pct(float(row["max_drawdown"])))


def _extract_date_range() -> tuple[date | None, date | None]:
    bankroll_df = load_mart("fact_bankroll_evolution")
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


def build_global_filters() -> GlobalFilters:
    strategy_df = load_mart("mart_strategy_performance")
    league_df = load_mart("mart_league_performance")
    market_df = load_mart("mart_market_performance")
    scenario_df = load_mart("mart_bankroll_scenarios_summary")
    min_date, max_date = _extract_date_range()

    strategy_options = _options(strategy_df, "strategy")
    league_options = _options(league_df, "league")
    market_options = _options(market_df, "market")
    method_options = _options(scenario_df, "method")
    market_label_to_code = {to_market_label(code): code for code in market_options}
    market_label_options = list(market_label_to_code.keys())

    st.sidebar.markdown("## Global Filters")
    strategies = st.sidebar.multiselect(
        "Strategies",
        options=strategy_options,
        default=strategy_options,
        key="global_strategies",
    )
    leagues = st.sidebar.multiselect(
        "Leagues",
        options=league_options,
        default=league_options,
        key="global_leagues",
    )
    selected_market_labels = st.sidebar.multiselect(
        "Markets",
        options=market_label_options,
        default=market_label_options,
        key="global_markets",
    )
    markets = [market_label_to_code[label] for label in selected_market_labels]
    methods = st.sidebar.multiselect(
        "Simulation Methods",
        options=method_options,
        default=method_options,
        key="global_methods",
    )

    if min_date and max_date:
        date_range = st.sidebar.date_input(
            "Date Range",
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

    st.sidebar.caption("Filters apply to any matching columns on each page.")
    return GlobalFilters(
        strategies=strategies,
        leagues=leagues,
        markets=markets,
        methods=methods,
        start_date=start_date,
        end_date=end_date,
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


def to_market_label(value: str) -> str:
    return MARKET_LABELS.get(str(value), str(value))


def apply_market_labels(df: pd.DataFrame, column: str = "market") -> pd.DataFrame:
    if df.empty or column not in df.columns:
        return df
    out = df.copy()
    out[column] = out[column].map(to_market_label)
    return out


def compact_table(
    df: pd.DataFrame,
    columns: list[str],
    *,
    rename: dict[str, str] | None = None,
    sort_by: str | None = None,
    ascending: bool = False,
    top_n: int | None = None,
    round_map: dict[str, int] | None = None,
    pct_cols: list[str] | None = None,
) -> pd.DataFrame:
    if df.empty:
        return df

    out = df.copy()
    if sort_by and sort_by in out.columns:
        out = out.sort_values(sort_by, ascending=ascending, na_position="last")
    if top_n:
        out = out.head(top_n)

    selected = [col for col in columns if col in out.columns]
    out = out[selected].copy()

    if round_map:
        for col, digits in round_map.items():
            if col in out.columns:
                out[col] = pd.to_numeric(out[col], errors="coerce").round(digits)

    for col in pct_cols or []:
        if col in out.columns:
            values = pd.to_numeric(out[col], errors="coerce") * 100
            out[col] = values.round(2).map(lambda v: f"{v:.2f}%" if pd.notna(v) else "-")

    if rename:
        out = out.rename(columns=rename)

    return out.reset_index(drop=True)
