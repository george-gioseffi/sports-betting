from __future__ import annotations

import plotly.express as px
import streamlit as st

from app.common import (
    PROFILE_LABELS,
    apply_chart_style,
    apply_global_filters,
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

st.set_page_config(
    page_title="Sports Betting Intelligence Engine",
    page_icon=":material/analytics:",
    layout="wide",
)

inject_styles()
filters = build_global_filters()
lang = filters.lang

render_page_header(t("home_title", lang), t("home_subtitle", lang))
render_section_note(t("home_note", lang))
st.info(t("home_info", lang))

overall = load_mart("kpi_overall")
monthly = apply_global_filters(load_mart("mart_monthly_performance"), filters)
risk = apply_global_filters(load_mart("mart_risk_scores"), filters)

if overall.empty:
    show_missing_data_message(lang)
else:
    render_kpi_strip(overall, lang)

left, right = st.columns([1.4, 1])

with left:
    st.subheader(t("home_workflow_title", lang))
    st.markdown(t("home_workflow_steps", lang))

    if not monthly.empty:
        fig_monthly = px.bar(
            monthly,
            x="month",
            y="pnl",
            color="yield_pct",
            title=t("home_monthly_title", lang),
            labels={
                "month": "Month" if lang == "en" else "Mês",
                "pnl": col_label("col_net_pnl", lang),
                "yield_pct": col_label("col_yield", lang),
            },
        )
        fig_monthly.update_yaxes(tickformat=",.0f")
        st.plotly_chart(apply_chart_style(fig_monthly), width="stretch")

with right:
    st.subheader(t("home_nav_title", lang))
    st.markdown(t("home_nav_items", lang))
    if not risk.empty:
        st.markdown(f"**{t('home_top_risk', lang)}**")
        top_risk = compact_table(
            risk,
            columns=["strategy", "risk_score", "risk_profile", "max_drawdown"],
            rename={
                "strategy": col_label("col_strategy", lang),
                "risk_score": col_label("col_risk_score", lang),
                "risk_profile": col_label("col_profile", lang),
                "max_drawdown": col_label("col_max_drawdown", lang),
            },
            sort_by="risk_score",
            ascending=False,
            top_n=4,
            round_map={"risk_score": 1},
            pct_cols=["max_drawdown"],
            decimal_cols=["risk_score"],
            value_maps={"risk_profile": PROFILE_LABELS.get(lang, PROFILE_LABELS["en"])},
            lang=lang,
        )
        st.dataframe(top_risk, width="stretch", hide_index=True)
