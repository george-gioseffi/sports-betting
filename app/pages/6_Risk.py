from __future__ import annotations

import plotly.express as px
import streamlit as st

from app.common import (
    apply_chart_style,
    apply_global_filters,
    build_global_filters,
    inject_styles,
    load_mart,
    render_page_header,
    render_section_note,
    show_missing_data_message,
)

inject_styles()
filters = build_global_filters()
render_page_header("Risk Governance Panel", "Risk scoring, governance posture, and concentration alert monitoring.")
render_section_note("This layer exists to prioritize capital preservation and decision discipline.")

risk_scores = apply_global_filters(load_mart("mart_risk_scores"), filters)
alerts = apply_global_filters(load_mart("mart_risk_alerts"), filters)

if risk_scores.empty:
    show_missing_data_message()
    st.stop()

c1, c2, c3 = st.columns(3)
c1.metric("Strategies Assessed", f"{risk_scores['strategy'].nunique()}")
c2.metric("Avg Risk Score", f"{risk_scores['risk_score'].mean():.1f}")
c3.metric("High Risk Strategies", f"{int((risk_scores['risk_profile'] == 'Aggressive').sum())}")

fig_risk = px.bar(
    risk_scores.sort_values("risk_score", ascending=False),
    x="strategy",
    y="risk_score",
    color="risk_profile",
    title="Risk Score by Strategy",
)
st.plotly_chart(apply_chart_style(fig_risk), width="stretch")

fig_components = px.scatter(
    risk_scores,
    x="max_drawdown",
    y="avg_stake_pct_bankroll",
    size="risk_score",
    color="volatility_score",
    hover_data=["strategy", "league_concentration", "max_red_streak"],
    title="Drawdown vs Stake Intensity",
)
st.plotly_chart(apply_chart_style(fig_components), width="stretch")

st.subheader("Risk Scores")
st.dataframe(
    risk_scores[
        [
            "strategy",
            "risk_score",
            "risk_profile",
            "max_drawdown",
            "avg_stake_pct_bankroll",
            "league_concentration",
            "max_red_streak",
        ]
    ],
    width="stretch",
)

if not alerts.empty:
    st.subheader("Risk Alerts")
    st.dataframe(alerts, width="stretch")

