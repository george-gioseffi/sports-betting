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
    inject_styles,
    load_mart,
    render_page_header,
    render_section_note,
    show_missing_data_message,
    t,
)

DQ_STATUS = {
    "en": {"passed": "Passed", "failed": "Failed"},
    "pt": {"passed": "Aprovado", "failed": "Falhou"},
}

DQ_SEVERITY = {
    "en": {"error": "Critical", "warning": "Warning"},
    "pt": {"error": "Crítica", "warning": "Alerta"},
}

inject_styles()
filters = build_global_filters()
lang = filters.lang

render_page_header(t("dq_title", lang), t("dq_subtitle", lang))
render_section_note(t("dq_note", lang))

dq = apply_global_filters(load_mart("data_quality_report"), filters)
if dq.empty:
    show_missing_data_message(lang)
    st.stop()

status_map = DQ_STATUS.get(lang, DQ_STATUS["en"])
severity_map = DQ_SEVERITY.get(lang, DQ_SEVERITY["en"])

dq_plot = dq.copy()
dq_plot["status_label"] = dq_plot["status"].astype(str).map(lambda value: status_map.get(value, value))
dq_plot["severity_label"] = dq_plot["severity"].astype(str).map(
    lambda value: severity_map.get(value, value)
)

summary = dq_plot.groupby(["status_label", "severity_label"], as_index=False)["check_name"].count()
summary = summary.rename(columns={"check_name": "checks"})

c1, c2, c3 = st.columns(3)
c1.metric(t("dq_total_checks", lang), format_int(summary["checks"].sum(), lang))
c2.metric(t("dq_failed_checks", lang), format_int(dq[dq["status"] == "failed"].shape[0], lang))
c3.metric(
    t("dq_critical_fails", lang),
    format_int(dq[(dq["status"] == "failed") & (dq["severity"] == "error")].shape[0], lang),
)

fig = px.bar(
    summary,
    x="severity_label",
    y="checks",
    color="status_label",
    barmode="group",
    title=t("dq_chart", lang),
    labels={
        "severity_label": col_label("col_severity", lang),
        "checks": t("dq_total_checks", lang),
        "status_label": col_label("col_status", lang),
    },
)
st.plotly_chart(apply_chart_style(fig), width="stretch")

dq_table = compact_table(
    dq,
    columns=["check_name", "status", "severity", "failed_rows", "details"],
    rename={
        "check_name": col_label("col_check", lang),
        "status": col_label("col_status", lang),
        "severity": col_label("col_severity", lang),
        "failed_rows": col_label("col_failed_rows", lang),
        "details": col_label("col_details", lang),
    },
    sort_by="failed_rows",
    ascending=False,
    top_n=12,
    int_cols=["failed_rows"],
    value_maps={"status": status_map, "severity": severity_map},
    lang=lang,
)
st.dataframe(dq_table, width="stretch", hide_index=True)
