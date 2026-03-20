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
    inject_styles,
    load_mart,
    render_kpi_strip,
    render_page_header,
    render_section_note,
    show_missing_data_message,
    t,
)

inject_styles()
filters = build_global_filters()
lang = filters.lang

render_page_header(t("overview_title", lang), t("overview_subtitle", lang))
render_section_note(t("overview_note", lang))

overall = load_mart("kpi_overall")
monthly = apply_global_filters(load_mart("mart_monthly_performance"), filters)
league = apply_global_filters(load_mart("mart_league_performance"), filters)
market = apply_global_filters(load_mart("mart_market_performance"), filters)
market = apply_market_labels(market, lang)

if overall.empty:
    show_missing_data_message(lang)
    st.stop()

render_kpi_strip(overall, lang)

if not monthly.empty:
    fig_monthly = px.bar(
        monthly,
        x="month",
        y="pnl",
        color="yield_pct",
        title=t("overview_monthly_title", lang),
        labels={
            "month": "Month" if lang == "en" else "Mês",
            "pnl": col_label("col_net_pnl", lang),
            "yield_pct": col_label("col_yield", lang),
        },
    )
    fig_monthly.update_yaxes(tickformat=",.0f")
    st.plotly_chart(apply_chart_style(fig_monthly), width="stretch")

col_a, col_b = st.columns(2)
with col_a:
    if not league.empty:
        fig_league = px.bar(
            league.sort_values("net_profit", ascending=False),
            x="league",
            y="net_profit",
            color="yield_pct",
            title=t("overview_net_by_league", lang),
            labels={
                "league": col_label("col_league", lang),
                "net_profit": col_label("col_net_pnl", lang),
                "yield_pct": col_label("col_yield", lang),
            },
        )
        fig_league.update_yaxes(tickformat=",.0f")
        st.plotly_chart(apply_chart_style(fig_league), width="stretch")

with col_b:
    if not market.empty:
        fig_market = px.bar(
            market.sort_values("yield_pct", ascending=False),
            x="market",
            y="yield_pct",
            color="avg_clv",
            title=t("overview_yield_by_market", lang),
            labels={
                "market": col_label("col_market", lang),
                "yield_pct": col_label("col_yield", lang),
                "avg_clv": col_label("col_avg_clv", lang),
            },
        )
        fig_market.update_yaxes(tickformat=".1%")
        st.plotly_chart(apply_chart_style(fig_market), width="stretch")

table_left, table_right = st.columns(2)
with table_left:
    if not league.empty:
        st.caption(t("overview_league_rank", lang))
        league_table = compact_table(
            league,
            columns=["league", "total_bets", "net_profit", "yield_pct", "max_drawdown"],
            rename={
                "league": col_label("col_league", lang),
                "total_bets": col_label("col_bets", lang),
                "net_profit": col_label("col_net_pnl", lang),
                "yield_pct": col_label("col_yield", lang),
                "max_drawdown": col_label("col_max_drawdown", lang),
            },
            sort_by="net_profit",
            ascending=False,
            top_n=6,
            pct_cols=["yield_pct", "max_drawdown"],
            int_cols=["total_bets"],
            decimal_cols=["net_profit"],
            lang=lang,
        )
        st.dataframe(league_table, width="stretch", hide_index=True)

with table_right:
    if not market.empty:
        st.caption(t("overview_market_rank", lang))
        market_table = compact_table(
            market,
            columns=["market", "total_bets", "net_profit", "yield_pct", "avg_clv"],
            rename={
                "market": col_label("col_market", lang),
                "total_bets": col_label("col_bets", lang),
                "net_profit": col_label("col_net_pnl", lang),
                "yield_pct": col_label("col_yield", lang),
                "avg_clv": col_label("col_avg_clv", lang),
            },
            sort_by="yield_pct",
            ascending=False,
            top_n=6,
            pct_cols=["yield_pct", "avg_clv"],
            int_cols=["total_bets"],
            decimal_cols=["net_profit"],
            lang=lang,
        )
        st.dataframe(market_table, width="stretch", hide_index=True)
