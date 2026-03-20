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
render_page_header(
    "Bankroll Simulation",
    "Compare capital trajectories across fixed stake, percentage stake, and fractional Kelly.",
)
render_section_note("Scenario analysis focuses on return versus drawdown trade-offs under risk constraints.")

scenario_runs = apply_global_filters(load_mart("fact_bankroll_scenarios"), filters)
scenario_summary = apply_global_filters(load_mart("mart_bankroll_scenarios_summary"), filters)

if scenario_runs.empty or scenario_summary.empty:
    show_missing_data_message()
    st.stop()

c1, c2, c3 = st.columns(3)
best_row = scenario_summary.sort_values("roi", ascending=False).iloc[0]
c1.metric("Scenarios", f"{scenario_summary['method'].nunique()}")
c2.metric("Best Method", str(best_row["method"]))
c3.metric("Best ROI", f"{float(best_row['roi']) * 100:.2f}%")

fig_curve = px.line(
    scenario_runs,
    x="placed_ts",
    y="bankroll_after",
    color="method",
    title="Bankroll Evolution by Scenario",
)
st.plotly_chart(apply_chart_style(fig_curve), width="stretch")

fig_drawdown = px.line(
    scenario_runs,
    x="placed_ts",
    y="drawdown",
    color="method",
    title="Drawdown Trajectory by Scenario",
)
st.plotly_chart(apply_chart_style(fig_drawdown), width="stretch")

st.dataframe(
    scenario_summary[
        ["method", "final_bankroll", "net_profit", "roi", "max_drawdown", "executed_bets", "skipped_bets"]
    ].sort_values("roi", ascending=False),
    width="stretch",
)

