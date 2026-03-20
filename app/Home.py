from __future__ import annotations

import plotly.express as px
import streamlit as st

from app.common import (
    apply_chart_style,
    apply_global_filters,
    build_global_filters,
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
    "End-to-end analytics platform for strategy performance, risk governance, and capital preservation.",
)
render_section_note(
    "Portfolio case focused on analytical decision quality, volatility control, and transparent risk monitoring."
)

st.info(
    "This project is for analytical, educational, and portfolio purposes only. It is not financial or betting advice."
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
        top_risk = risk.sort_values("risk_score", ascending=False).head(3)
        st.markdown("**Top Risk Exposure (Filtered)**")
        st.dataframe(top_risk[["strategy", "risk_score", "risk_profile"]], width="stretch")

