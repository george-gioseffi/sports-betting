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
    render_kpi_strip,
    render_page_header,
    render_section_note,
    show_missing_data_message,
)

inject_styles()
filters = build_global_filters()
render_page_header("Overview", "Top-line performance health and trend monitoring.")
render_section_note("Use this page to evaluate portfolio-level quality before strategy deep dives.")

overall = load_mart("kpi_overall")
monthly = apply_global_filters(load_mart("mart_monthly_performance"), filters)
league = apply_global_filters(load_mart("mart_league_performance"), filters)
market = apply_global_filters(load_mart("mart_market_performance"), filters)
market = apply_market_labels(market, "market")

if overall.empty:
    show_missing_data_message()
    st.stop()

render_kpi_strip(overall)

if not monthly.empty:
    fig_monthly = px.bar(
        monthly,
        x="month",
        y="pnl",
        title="Monthly Net Profit",
        labels={"month": "Month", "pnl": "Net Profit"},
    )
    st.plotly_chart(apply_chart_style(fig_monthly), width="stretch")

col_a, col_b = st.columns(2)
with col_a:
    if not league.empty:
        fig_league = px.bar(
            league.sort_values("net_profit", ascending=False),
            x="league",
            y="net_profit",
            color="yield_pct",
            title="Net Profit by League",
            labels={"yield_pct": "Yield"},
        )
        st.plotly_chart(apply_chart_style(fig_league), width="stretch")

with col_b:
    if not market.empty:
        fig_market = px.bar(
            market.sort_values("yield_pct", ascending=False),
            x="market",
            y="yield_pct",
            color="avg_clv",
            title="Yield by Market",
            labels={"yield_pct": "Yield", "avg_clv": "Avg CLV"},
        )
        st.plotly_chart(apply_chart_style(fig_market), width="stretch")

table_left, table_right = st.columns(2)
with table_left:
    if not league.empty:
        st.caption("League Ranking")
        league_table = compact_table(
            league,
            columns=["league", "total_bets", "net_profit", "yield_pct", "max_drawdown"],
            rename={
                "league": "League",
                "total_bets": "Bets",
                "net_profit": "Net P&L",
                "yield_pct": "Yield",
                "max_drawdown": "Max Drawdown",
            },
            sort_by="net_profit",
            ascending=False,
            top_n=5,
            round_map={"net_profit": 2},
            pct_cols=["yield_pct", "max_drawdown"],
        )
        st.dataframe(league_table, width="stretch", hide_index=True)

with table_right:
    if not market.empty:
        st.caption("Market Ranking")
        market_table = compact_table(
            market,
            columns=["market", "total_bets", "net_profit", "yield_pct", "avg_clv"],
            rename={
                "market": "Market",
                "total_bets": "Bets",
                "net_profit": "Net P&L",
                "yield_pct": "Yield",
                "avg_clv": "Avg CLV",
            },
            sort_by="yield_pct",
            ascending=False,
            top_n=5,
            round_map={"net_profit": 2},
            pct_cols=["yield_pct", "avg_clv"],
        )
        st.dataframe(market_table, width="stretch", hide_index=True)

