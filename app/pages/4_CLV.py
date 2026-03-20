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
render_page_header("CLV Analysis", "Execution quality diagnostics using captured odds versus closing odds.")
render_section_note("Consistent positive CLV may indicate entry quality, even when short-term PnL fluctuates.")

strategy_perf = apply_global_filters(load_mart("mart_strategy_performance"), filters)
market_perf = apply_global_filters(load_mart("mart_market_performance"), filters)
bookmaker_perf = apply_global_filters(load_mart("mart_bookmaker_performance"), filters)

if strategy_perf.empty:
    show_missing_data_message()
    st.stop()

c1, c2, c3 = st.columns(3)
c1.metric("Strategies", f"{strategy_perf['strategy'].nunique()}")
c2.metric("Avg CLV (Filtered)", f"{strategy_perf['avg_clv'].mean() * 100:.2f}%")
c3.metric("Net Profit (Filtered)", f"{strategy_perf['net_profit'].sum():.2f}")

fig_strategy = px.scatter(
    strategy_perf,
    x="avg_clv",
    y="yield_pct",
    size="total_bets",
    color="net_profit",
    text="strategy",
    title="Strategy CLV vs Yield",
)
fig_strategy.update_traces(textposition="top center")
st.plotly_chart(apply_chart_style(fig_strategy), width="stretch")

if not market_perf.empty:
    fig_market = px.bar(
        market_perf.sort_values("avg_clv", ascending=False),
        x="market",
        y="avg_clv",
        color="yield_pct",
        title="Average CLV by Market",
    )
    st.plotly_chart(apply_chart_style(fig_market), width="stretch")

if not bookmaker_perf.empty:
    st.subheader("Bookmaker CLV Distribution")
    st.dataframe(
        bookmaker_perf[
            ["bookmaker", "total_bets", "avg_clv", "yield_pct", "net_profit"]
        ].sort_values("avg_clv", ascending=False),
        width="stretch",
    )

