from __future__ import annotations

import plotly.express as px
import streamlit as st

from app.common import (
    PROFILE_LABELS,
    apply_chart_style,
    apply_global_filters,
    build_global_filters,
    col_label,
    compact_table,
    format_int,
    format_number,
    inject_styles,
    load_mart,
    render_page_header,
    render_section_note,
    show_missing_data_message,
    t,
)

inject_styles()
filters = build_global_filters()
lang = filters.lang

render_page_header(t("strategies_title", lang), t("strategies_subtitle", lang))
render_section_note(t("strategies_note", lang))

strategy_perf = apply_global_filters(load_mart("mart_strategy_performance"), filters)
risk_scores = apply_global_filters(load_mart("mart_risk_scores"), filters)

if strategy_perf.empty:
    show_missing_data_message(lang)
    st.stop()

if risk_scores.empty or "strategy" not in risk_scores.columns:
    risk_scores = strategy_perf[["strategy"]].copy()
    risk_scores["risk_score"] = float("nan")
    risk_scores["risk_profile"] = "N/A"
    risk_scores["max_drawdown"] = float("nan")
    risk_scores["max_red_streak"] = float("nan")

joined = strategy_perf.merge(risk_scores, on="strategy", how="left", suffixes=("", "_risk"))

if "avg_clv_risk" in joined.columns and "avg_clv" not in joined.columns:
    joined["avg_clv"] = joined["avg_clv_risk"]
if "max_drawdown_risk" in joined.columns:
    joined["max_drawdown"] = joined["max_drawdown_risk"]
if "max_red_streak_risk" in joined.columns:
    joined["max_red_streak"] = joined["max_red_streak_risk"]

plot_df = joined.copy()
plot_df["risk_profile_label"] = plot_df["risk_profile"].astype(str).map(
    lambda value: PROFILE_LABELS.get(lang, PROFILE_LABELS["en"]).get(value, value)
)

c1, c2, c3 = st.columns(3)
c1.metric(t("strategies_count", lang), format_int(plot_df["strategy"].nunique(), lang))
c2.metric(t("strategies_filtered_pnl", lang), format_number(plot_df["net_profit"].sum(), lang, 2))
mean_risk = plot_df["risk_score"].mean() if "risk_score" in plot_df.columns else float("nan")
c3.metric(t("strategies_avg_risk", lang), format_number(mean_risk, lang, 1))

fig = px.bar(
    plot_df.sort_values("net_profit", ascending=False),
    x="strategy",
    y="net_profit",
    color="risk_profile_label",
    title=t("strategies_profit_risk", lang),
    labels={
        "strategy": col_label("col_strategy", lang),
        "net_profit": col_label("col_net_pnl", lang),
        "risk_profile_label": col_label("col_profile", lang),
    },
)
fig.update_yaxes(tickformat=",.0f")
st.plotly_chart(apply_chart_style(fig), width="stretch")

scatter = px.scatter(
    plot_df,
    x="avg_clv",
    y="yield_pct",
    size="total_bets",
    color="risk_score",
    hover_data=["strategy", "max_drawdown", "max_red_streak"],
    title=t("strategies_exec_quality", lang),
    labels={
        "avg_clv": col_label("col_avg_clv", lang),
        "yield_pct": col_label("col_yield", lang),
        "risk_score": col_label("col_risk_score", lang),
        "total_bets": col_label("col_bets", lang),
    },
)
scatter.update_xaxes(tickformat=".1%")
scatter.update_yaxes(tickformat=".1%")
st.plotly_chart(apply_chart_style(scatter), width="stretch")

scorecard = compact_table(
    plot_df,
    columns=[
        "strategy",
        "total_bets",
        "net_profit",
        "yield_pct",
        "avg_clv",
        "max_drawdown",
        "risk_score",
        "risk_profile",
    ],
    rename={
        "strategy": col_label("col_strategy", lang),
        "total_bets": col_label("col_bets", lang),
        "net_profit": col_label("col_net_pnl", lang),
        "yield_pct": col_label("col_yield", lang),
        "avg_clv": col_label("col_avg_clv", lang),
        "max_drawdown": col_label("col_max_drawdown", lang),
        "risk_score": col_label("col_risk_score", lang),
        "risk_profile": col_label("col_profile", lang),
    },
    sort_by="risk_score",
    ascending=False,
    pct_cols=["yield_pct", "avg_clv", "max_drawdown"],
    int_cols=["total_bets"],
    decimal_cols=["net_profit", "risk_score"],
    round_map={"risk_score": 1},
    value_maps={"risk_profile": PROFILE_LABELS.get(lang, PROFILE_LABELS["en"])},
    lang=lang,
)
st.dataframe(scorecard, width="stretch", hide_index=True)
