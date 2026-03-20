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

render_page_header(t("clv_title", lang), t("clv_subtitle", lang))
render_section_note(t("clv_note", lang))

strategy_perf = apply_global_filters(load_mart("mart_strategy_performance"), filters)
market_perf = apply_global_filters(load_mart("mart_market_performance"), filters)
bookmaker_perf = apply_global_filters(load_mart("mart_bookmaker_performance"), filters)

if strategy_perf.empty:
    show_missing_data_message(lang)
    st.stop()
market_perf = apply_market_labels(market_perf, lang)

c1, c2, c3 = st.columns(3)
c1.metric(t("clv_strategies", lang), format_int(strategy_perf["strategy"].nunique(), lang))
c2.metric(t("clv_avg", lang), format_pct(strategy_perf["avg_clv"].mean(), lang, 2))
c3.metric(t("clv_net", lang), format_number(strategy_perf["net_profit"].sum(), lang, 2))

fig_strategy = px.scatter(
    strategy_perf,
    x="avg_clv",
    y="yield_pct",
    size="total_bets",
    color="net_profit",
    text="strategy",
    title=t("clv_scatter", lang),
    labels={
        "avg_clv": col_label("col_avg_clv", lang),
        "yield_pct": col_label("col_yield", lang),
        "net_profit": col_label("col_net_pnl", lang),
    },
)
fig_strategy.update_traces(textposition="top center")
fig_strategy.update_xaxes(tickformat=".1%")
fig_strategy.update_yaxes(tickformat=".1%")
st.plotly_chart(apply_chart_style(fig_strategy), width="stretch")

if not market_perf.empty:
    fig_market = px.bar(
        market_perf.sort_values("avg_clv", ascending=False),
        x="market",
        y="avg_clv",
        color="yield_pct",
        title=t("clv_market", lang),
        labels={
            "market": col_label("col_market", lang),
            "avg_clv": col_label("col_avg_clv", lang),
            "yield_pct": col_label("col_yield", lang),
        },
    )
    fig_market.update_yaxes(tickformat=".1%")
    st.plotly_chart(apply_chart_style(fig_market), width="stretch")

if not bookmaker_perf.empty:
    st.subheader(t("clv_bookmaker_summary", lang))
    bookmaker_table = compact_table(
        bookmaker_perf,
        columns=["bookmaker", "total_bets", "avg_clv", "yield_pct", "net_profit"],
        rename={
            "bookmaker": col_label("col_bookmaker", lang),
            "total_bets": col_label("col_bets", lang),
            "avg_clv": col_label("col_avg_clv", lang),
            "yield_pct": col_label("col_yield", lang),
            "net_profit": col_label("col_net_pnl", lang),
        },
        sort_by="avg_clv",
        ascending=False,
        pct_cols=["avg_clv", "yield_pct"],
        int_cols=["total_bets"],
        decimal_cols=["net_profit"],
        lang=lang,
    )
    st.dataframe(bookmaker_table, width="stretch", hide_index=True)
