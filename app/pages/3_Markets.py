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
render_page_header("Market Analysis", "Compare market families by profitability, hit rate, and execution quality.")
render_section_note("Markets with higher raw return can still present unstable drawdown behavior.")

market_perf = apply_global_filters(load_mart("mart_market_performance"), filters)
if market_perf.empty:
    show_missing_data_message()
    st.stop()

c1, c2, c3 = st.columns(3)
c1.metric("Markets", f"{market_perf['market'].nunique()}")
c2.metric("Filtered Net Profit", f"{market_perf['net_profit'].sum():.2f}")
c3.metric("Avg Yield", f"{market_perf['yield_pct'].mean() * 100:.2f}%")

fig_net = px.bar(
    market_perf.sort_values("net_profit", ascending=False),
    x="market",
    y="net_profit",
    color="yield_pct",
    title="Net Profit by Market",
)
st.plotly_chart(apply_chart_style(fig_net), width="stretch")

fig_yield = px.scatter(
    market_perf,
    x="avg_odds",
    y="yield_pct",
    size="total_bets",
    color="avg_clv",
    hover_data=["market", "win_rate", "max_drawdown"],
    title="Odds Level vs Yield by Market",
)
st.plotly_chart(apply_chart_style(fig_yield), width="stretch")

st.dataframe(
    market_perf[
        ["market", "total_bets", "avg_odds", "win_rate", "yield_pct", "avg_clv", "max_drawdown"]
    ].sort_values("yield_pct", ascending=False),
    width="stretch",
)

