from __future__ import annotations

import plotly.express as px
import streamlit as st

from app.common import (
    apply_chart_style,
    apply_global_filters,
    build_global_filters,
    compact_table,
    inject_styles,
    load_mart,
    render_kpi_strip,
    render_page_header,
    render_section_note,
    show_missing_data_message,
)

st.set_page_config(
    page_title="Sports Betting Intelligence Engine",
    page_icon=":material/analytics:",
    layout="wide",
)

inject_styles()
filters = build_global_filters()
render_page_header(
    "Sports Betting Intelligence Engine",
    "Analytics platform for performance quality, risk governance, and capital preservation.",
)
render_section_note(
    "Portfolio case focused on decision quality, volatility control, and transparent risk monitoring."
)

st.info(
    "Analytical and educational project. Not financial or betting advice."
)

overall = load_mart("kpi_overall")
monthly = apply_global_filters(load_mart("mart_monthly_performance"), filters)
risk = apply_global_filters(load_mart("mart_risk_scores"), filters)
if overall.empty:
    show_missing_data_message()
else:
    render_kpi_strip(overall)

left, right = st.columns([1.4, 1])

with left:
    st.subheader("Analytics Workflow")
    st.markdown(
        """
1. Ingest match and odds events into `raw`.
2. Standardize records in `staging` with quality checks.
3. Materialize KPI marts and risk layers.
4. Compare scenarios in bankroll simulation.
5. Expose insights in executive + exploratory dashboards.
"""
    )

    if not monthly.empty:
        fig_monthly = px.bar(
            monthly,
            x="month",
            y="pnl",
            color="yield_pct",
            title="Monthly Performance Snapshot",
            labels={"pnl": "Net Profit", "yield_pct": "Yield"},
        )
        st.plotly_chart(apply_chart_style(fig_monthly), width="stretch")

with right:
    st.subheader("Navigation")
    st.markdown(
        """
- **Overview:** KPI health and trend context.
- **Strategies:** return vs risk profile analysis.
- **Markets:** performance by market type.
- **CLV:** execution quality diagnostics.
- **Bankroll:** scenario and drawdown comparison.
- **Risk:** governance score and alerts.
- **Data Quality:** quality contract monitoring.
"""
    )
    if not risk.empty:
        st.markdown("**Highest Risk Exposure (Filtered)**")
        top_risk = compact_table(
            risk,
            columns=["strategy", "risk_score", "risk_profile", "max_drawdown"],
            rename={
                "strategy": "Strategy",
                "risk_score": "Risk Score",
                "risk_profile": "Profile",
                "max_drawdown": "Max Drawdown",
            },
            sort_by="risk_score",
            ascending=False,
            top_n=4,
            round_map={"risk_score": 1},
            pct_cols=["max_drawdown"],
        )
        st.dataframe(top_risk, width="stretch", hide_index=True)

