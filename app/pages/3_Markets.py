from __future__ import annotations

import plotly.express as px
import streamlit as st

from app.common import (
    apply_chart_style,
    apply_global_filters,
    apply_market_labels,
    build_global_filters,
    col_label,
    compact_table,
    format_int,
    format_number,
    format_pct,
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

render_page_header(t("markets_title", lang), t("markets_subtitle", lang))
render_section_note(t("markets_note", lang))

market_perf = apply_global_filters(load_mart("mart_market_performance"), filters)
if market_perf.empty:
    show_missing_data_message(lang)
    st.stop()
market_perf = apply_market_labels(market_perf, lang)

c1, c2, c3 = st.columns(3)
c1.metric(t("markets_count", lang), format_int(market_perf["market"].nunique(), lang))
c2.metric(t("markets_filtered_pnl", lang), format_number(market_perf["net_profit"].sum(), lang, 2))
c3.metric(t("markets_avg_yield", lang), format_pct(market_perf["yield_pct"].mean(), lang, 2))

fig_net = px.bar(
    market_perf.sort_values("net_profit", ascending=False),
    x="market",
    y="net_profit",
    color="yield_pct",
    title=t("markets_net_by_market", lang),
    labels={
        "market": col_label("col_market", lang),
        "net_profit": col_label("col_net_pnl", lang),
        "yield_pct": col_label("col_yield", lang),
    },
)
fig_net.update_yaxes(tickformat=",.0f")
st.plotly_chart(apply_chart_style(fig_net), width="stretch")

fig_yield = px.scatter(
    market_perf,
    x="avg_odds",
    y="yield_pct",
    size="total_bets",
    color="avg_clv",
    hover_data=["market", "win_rate", "max_drawdown"],
    title=t("markets_odds_vs_yield", lang),
    labels={
        "avg_odds": "Odds",
        "yield_pct": col_label("col_yield", lang),
        "avg_clv": col_label("col_avg_clv", lang),
        "total_bets": col_label("col_bets", lang),
    },
)
fig_yield.update_yaxes(tickformat=".1%")
st.plotly_chart(apply_chart_style(fig_yield), width="stretch")

market_table = compact_table(
    market_perf,
    columns=["market", "total_bets", "net_profit", "yield_pct", "win_rate", "avg_clv", "max_drawdown"],
    rename={
        "market": col_label("col_market", lang),
        "total_bets": col_label("col_bets", lang),
        "net_profit": col_label("col_net_pnl", lang),
        "yield_pct": col_label("col_yield", lang),
        "win_rate": col_label("col_win_rate", lang),
        "avg_clv": col_label("col_avg_clv", lang),
        "max_drawdown": col_label("col_max_drawdown", lang),
    },
    sort_by="net_profit",
    ascending=False,
    pct_cols=["yield_pct", "win_rate", "avg_clv", "max_drawdown"],
    int_cols=["total_bets"],
    decimal_cols=["net_profit"],
    lang=lang,
)
st.dataframe(market_table, width="stretch", hide_index=True)
