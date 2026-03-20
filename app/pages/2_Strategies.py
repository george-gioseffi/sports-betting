from __future__ import annotations

import plotly.express as px
import streamlit as st

from app.common import (
    apply_chart_style,
    apply_global_filters,
    build_global_filters,
    compact_table,
    inject_styles,
    load_mart,
    render_page_header,
    render_section_note,
    show_missing_data_message,
)

inject_styles()
filters = build_global_filters()
render_page_header("Strategy Analysis", "Return quality and risk posture by strategy.")
render_section_note("A strong strategy combines edge, discipline, and stable drawdown.")

strategy_perf = apply_global_filters(load_mart("mart_strategy_performance"), filters)
risk_scores = apply_global_filters(load_mart("mart_risk_scores"), filters)

if strategy_perf.empty:
    show_missing_data_message()
    st.stop()

if risk_scores.empty or "strategy" not in risk_scores.columns:
    risk_scores = strategy_perf[["strategy"]].copy()
    risk_scores["risk_score"] = float("nan")
    risk_scores["risk_profile"] = "N/A"
    risk_scores["max_drawdown"] = float("nan")
    risk_scores["max_red_streak"] = float("nan")

joined = strategy_perf.merge(risk_scores, on="strategy", how="left")

for base_col in ["avg_clv", "max_drawdown", "max_red_streak"]:
    left_col = f"{base_col}_x"
    right_col = f"{base_col}_y"
    if left_col in joined.columns:
        joined[base_col] = joined[left_col]
    elif right_col in joined.columns:
        joined[base_col] = joined[right_col]

c1, c2, c3 = st.columns(3)
c1.metric("Strategies", f"{joined['strategy'].nunique()}")
c2.metric("Filtered Net Profit", f"{joined['net_profit'].sum():.2f}")
c3.metric("Avg Risk Score", f"{joined['risk_score'].mean():.1f}" if "risk_score" in joined else "N/A")

fig = px.bar(
    joined.sort_values("net_profit", ascending=False),
    x="strategy",
    y="net_profit",
    color="risk_profile",
    title="Net Profit and Risk Profile by Strategy",
)
st.plotly_chart(apply_chart_style(fig), width="stretch")

scatter = px.scatter(
    joined,
    x="avg_clv",
    y="yield_pct",
    size="total_bets",
    color="risk_score",
    hover_data=["strategy", "max_drawdown", "max_red_streak"],
    title="Execution Quality vs Return Efficiency",
)
st.plotly_chart(apply_chart_style(scatter), width="stretch")

scorecard = compact_table(
    joined,
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
        "strategy": "Strategy",
        "total_bets": "Bets",
        "net_profit": "Net P&L",
        "yield_pct": "Yield",
        "avg_clv": "Avg CLV",
        "max_drawdown": "Max Drawdown",
        "risk_score": "Risk Score",
        "risk_profile": "Profile",
    },
    sort_by="risk_score",
    ascending=False,
    round_map={"net_profit": 2, "risk_score": 1},
    pct_cols=["yield_pct", "avg_clv", "max_drawdown"],
)
st.dataframe(scorecard, width="stretch", hide_index=True)

