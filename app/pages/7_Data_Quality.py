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
    render_page_header,
    render_section_note,
    show_missing_data_message,
)

inject_styles()
filters = build_global_filters()
render_page_header("Data Quality Dashboard", "Validation status across critical and warning checks.")
render_section_note("Quality gates protect metric credibility before interpretation.")

dq = apply_global_filters(load_mart("data_quality_report"), filters)
if dq.empty:
    show_missing_data_message()
    st.stop()

summary = dq.groupby(["status", "severity"], as_index=False)["check_name"].count()
summary = summary.rename(columns={"check_name": "checks"})
c1, c2, c3 = st.columns(3)
c1.metric("Total Checks", f"{int(summary['checks'].sum())}")
c2.metric("Failed Checks", f"{int(dq[dq['status'] == 'failed'].shape[0])}")
c3.metric("Critical Fails", f"{int(dq[(dq['status'] == 'failed') & (dq['severity'] == 'error')].shape[0])}")

fig = px.bar(
    summary,
    x="severity",
    y="checks",
    color="status",
    barmode="group",
    title="Validation Checks by Severity and Status",
)
st.plotly_chart(apply_chart_style(fig), width="stretch")

dq_table = compact_table(
    dq,
    columns=["check_name", "status", "severity", "failed_rows", "details"],
    rename={
        "check_name": "Check",
        "status": "Status",
        "severity": "Severity",
        "failed_rows": "Failed Rows",
        "details": "Details",
    },
    sort_by="failed_rows",
    ascending=False,
    top_n=12,
)
st.dataframe(dq_table, width="stretch", hide_index=True)

