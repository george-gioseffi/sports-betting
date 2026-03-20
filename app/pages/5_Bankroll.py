from __future__ import annotations

import plotly.express as px
import streamlit as st

from app.common import (
    apply_chart_style,
    apply_global_filters,
    build_global_filters,
    col_label,
    compact_table,
    format_int,
    format_pct,
    inject_styles,
    load_mart,
    render_page_header,
    render_section_note,
    show_missing_data_message,
    t,
)

METHOD_LABELS = {
    "en": {
        "fixed": "Fixed Stake",
        "percentage": "Percentage Stake",
        "kelly": "Fractional Kelly",
    },
    "pt": {
        "fixed": "Stake Fixa",
        "percentage": "Stake Percentual",
        "kelly": "Kelly Fracionado",
    },
}

inject_styles()
filters = build_global_filters()
lang = filters.lang

render_page_header(t("bankroll_title", lang), t("bankroll_subtitle", lang))
render_section_note(t("bankroll_note", lang))

scenario_runs = apply_global_filters(load_mart("fact_bankroll_scenarios"), filters)
scenario_summary = apply_global_filters(load_mart("mart_bankroll_scenarios_summary"), filters)

if scenario_runs.empty or scenario_summary.empty:
    show_missing_data_message(lang)
    st.stop()

method_map = METHOD_LABELS.get(lang, METHOD_LABELS["en"])
plot_runs = scenario_runs.copy()
plot_summary = scenario_summary.copy()
plot_runs["method_label"] = plot_runs["method"].astype(str).map(
    lambda value: method_map.get(value, value)
)
plot_summary["method_label"] = plot_summary["method"].astype(str).map(
    lambda value: method_map.get(value, value)
)

c1, c2, c3 = st.columns(3)
best_row = plot_summary.sort_values("roi", ascending=False).iloc[0]
c1.metric(t("bankroll_scenarios", lang), format_int(plot_summary["method"].nunique(), lang))
c2.metric(t("bankroll_best_method", lang), str(best_row["method_label"]))
c3.metric(t("bankroll_best_roi", lang), format_pct(best_row["roi"], lang, 2))

fig_curve = px.line(
    plot_runs,
    x="placed_ts",
    y="bankroll_after",
    color="method_label",
    title=t("bankroll_curve", lang),
    labels={
        "placed_ts": "Date" if lang == "en" else "Data",
        "bankroll_after": col_label("col_final_bankroll", lang),
        "method_label": col_label("col_method", lang),
    },
)
fig_curve.update_yaxes(tickformat=",.0f")
st.plotly_chart(apply_chart_style(fig_curve), width="stretch")

fig_drawdown = px.line(
    plot_runs,
    x="placed_ts",
    y="drawdown",
    color="method_label",
    title=t("bankroll_drawdown", lang),
    labels={
        "placed_ts": "Date" if lang == "en" else "Data",
        "drawdown": col_label("col_max_drawdown", lang),
        "method_label": col_label("col_method", lang),
    },
)
fig_drawdown.update_yaxes(tickformat=".1%")
st.plotly_chart(apply_chart_style(fig_drawdown), width="stretch")

scenario_table = compact_table(
    plot_summary,
    columns=[
        "method_label",
        "final_bankroll",
        "net_profit",
        "roi",
        "max_drawdown",
        "executed_bets",
        "skipped_bets",
    ],
    rename={
        "method_label": col_label("col_method", lang),
        "final_bankroll": col_label("col_final_bankroll", lang),
        "net_profit": col_label("col_net_pnl", lang),
        "roi": col_label("col_roi", lang),
        "max_drawdown": col_label("col_max_drawdown", lang),
        "executed_bets": col_label("col_executed_bets", lang),
        "skipped_bets": col_label("col_skipped_bets", lang),
    },
    sort_by="roi",
    ascending=False,
    pct_cols=["roi", "max_drawdown"],
    int_cols=["executed_bets", "skipped_bets"],
    decimal_cols=["final_bankroll", "net_profit"],
    lang=lang,
)
st.dataframe(scenario_table, width="stretch", hide_index=True)
