from __future__ import annotations

import plotly.express as px
import streamlit as st

from app.common import (
    apply_chart_style,
    apply_global_filters,
    apply_market_labels,
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
render_page_header("Market Analysis", "Performance comparison across market families.")
render_section_note("Focus on the trade-off between return, hit rate, and drawdown.")

market_perf = apply_global_filters(load_mart("mart_market_performance"), filters)
if market_perf.empty:
    show_missing_data_message()
    st.stop()
market_perf = apply_market_labels(market_perf, "market")

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

market_table = compact_table(
    market_perf,
    columns=["market", "total_bets", "net_profit", "yield_pct", "win_rate", "avg_clv", "max_drawdown"],
    rename={
        "market": "Market",
        "total_bets": "Bets",
        "net_profit": "Net P&L",
        "yield_pct": "Yield",
        "win_rate": "Win Rate",
        "avg_clv": "Avg CLV",
        "max_drawdown": "Max Drawdown",
    },
    sort_by="net_profit",
    ascending=False,
    round_map={"net_profit": 2},
    pct_cols=["yield_pct", "win_rate", "avg_clv", "max_drawdown"],
)
st.dataframe(market_table, width="stretch", hide_index=True)

