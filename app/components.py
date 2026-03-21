from __future__ import annotations

from pathlib import Path

import pandas as pd
import plotly.graph_objects as go
import streamlit as st

from app.formatting import format_int, format_number, format_pct
from app.translations import t

BASE_DIR = Path(__file__).resolve().parents[1]
MARTS_DIR = BASE_DIR / "data" / "marts"


@st.cache_data(show_spinner=False)
def load_mart(table_name: str) -> pd.DataFrame:
    path = MARTS_DIR / f"{table_name}.csv"
    if not path.exists():
        return pd.DataFrame()
    return pd.read_csv(path)


def show_missing_data_message(lang: str = "en") -> None:
    st.warning(t("missing_data_warning", lang))


def inject_styles() -> None:
    st.markdown(
        """
<style>
.block-container {
    max-width: 1380px;
    padding-top: 1.8rem;
    padding-bottom: 2rem;
}
.hero-title {
    font-size: 1.85rem;
    font-weight: 700;
    margin-bottom: 0.12rem;
}
.hero-subtitle {
    color: #4b5563;
    margin-bottom: 0.75rem;
}
.section-note {
    color: #6b7280;
    font-size: 0.92rem;
    margin-top: -0.15rem;
    margin-bottom: 0.75rem;
}
[data-testid="stMetric"] {
    background: #f8fafc;
    border: 1px solid #e5e7eb;
    border-radius: 10px;
    padding: 0.55rem 0.65rem;
}
[data-testid="stMetricLabel"] p {
    font-size: 0.84rem;
}
[data-testid="stMetricValue"] {
    font-size: 1.30rem;
}
div[data-testid="stDataFrame"] {
    border: 1px solid #e5e7eb;
    border-radius: 10px;
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


def render_kpi_strip(overall_df: pd.DataFrame, lang: str = "en") -> None:
    if overall_df.empty:
        return
    row = overall_df.iloc[0]
    c1, c2, c3, c4, c5, c6 = st.columns(6)
    c1.metric(t("kpi_total_bets", lang), format_int(row["total_bets"], lang))
    c2.metric(t("kpi_win_rate", lang), format_pct(row["win_rate"], lang))
    c3.metric(t("kpi_yield", lang), format_pct(row["yield_pct"], lang))
    c4.metric(t("kpi_roi", lang), format_pct(row["roi"], lang))
    c5.metric(t("kpi_avg_clv", lang), format_pct(row["avg_clv"], lang))
    c6.metric(t("kpi_max_drawdown", lang), format_pct(row["max_drawdown"], lang))


def compact_table(
    df: pd.DataFrame,
    columns: list[str],
    *,
    rename: dict[str, str] | None = None,
    sort_by: str | None = None,
    ascending: bool = False,
    top_n: int | None = None,
    lang: str = "en",
    round_map: dict[str, int] | None = None,
    pct_cols: list[str] | None = None,
    int_cols: list[str] | None = None,
    decimal_cols: list[str] | None = None,
    value_maps: dict[str, dict[str, str]] | None = None,
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

    for col, mapping in (value_maps or {}).items():
        if col in out.columns:
            out[col] = out[col].astype(str).map(lambda value, m=mapping: m.get(value, value))

    def precision(col: str, default: int) -> int:
        if not round_map:
            return default
        return int(round_map.get(col, default))

    for col in pct_cols or []:
        if col in out.columns:
            digits = precision(col, 2)
            values = pd.to_numeric(out[col], errors="coerce")
            out[col] = values.map(lambda value, d=digits: format_pct(value, lang, d))

    for col in int_cols or []:
        if col in out.columns:
            values = pd.to_numeric(out[col], errors="coerce")
            out[col] = values.map(lambda value: format_int(value, lang))

    for col in decimal_cols or []:
        if col in out.columns:
            digits = precision(col, 2)
            values = pd.to_numeric(out[col], errors="coerce")
            out[col] = values.map(lambda value, d=digits: format_number(value, lang, d))

    if rename:
        out = out.rename(columns=rename)

    return out.reset_index(drop=True)
