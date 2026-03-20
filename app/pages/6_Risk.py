from __future__ import annotations

import plotly.express as px
import streamlit as st

from app.common import (
    PROFILE_LABELS,
    SEVERITY_ORDER,
    SEVERITY_LABELS,
    ALERT_LABELS,
    apply_chart_style,
    apply_global_filters,
    build_global_filters,
    col_label,
    compact_table,
    format_int,
    format_number,
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

render_page_header(t("risk_title", lang), t("risk_subtitle", lang))
render_section_note(t("risk_note", lang))

risk_scores = apply_global_filters(load_mart("mart_risk_scores"), filters)
alerts = apply_global_filters(load_mart("mart_risk_alerts"), filters)

if risk_scores.empty:
    show_missing_data_message(lang)
    st.stop()

profile_map = PROFILE_LABELS.get(lang, PROFILE_LABELS["en"])
risk_plot = risk_scores.copy()
risk_plot["risk_profile_label"] = risk_plot["risk_profile"].astype(str).map(
    lambda value: profile_map.get(value, value)
)

c1, c2, c3 = st.columns(3)
c1.metric(t("risk_assessed", lang), format_int(risk_scores["strategy"].nunique(), lang))
c2.metric(t("risk_avg_score", lang), format_number(risk_scores["risk_score"].mean(), lang, 1))
high_risk_count = int((risk_scores["risk_profile"] == "Aggressive").sum())
c3.metric(t("risk_high_risk", lang), format_int(high_risk_count, lang))

fig_risk = px.bar(
    risk_plot.sort_values("risk_score", ascending=False),
    x="strategy",
    y="risk_score",
    color="risk_profile_label",
    title=t("risk_score_by_strategy", lang),
    labels={
        "strategy": col_label("col_strategy", lang),
        "risk_score": col_label("col_risk_score", lang),
        "risk_profile_label": col_label("col_profile", lang),
    },
)
st.plotly_chart(apply_chart_style(fig_risk), width="stretch")

fig_components = px.scatter(
    risk_scores,
    x="max_drawdown",
    y="avg_stake_pct_bankroll",
    size="risk_score",
    color="volatility_score",
    hover_data=["strategy", "league_concentration", "max_red_streak"],
    title=t("risk_drawdown_vs_stake", lang),
    labels={
        "max_drawdown": col_label("col_max_drawdown", lang),
        "avg_stake_pct_bankroll": col_label("col_avg_stake_pct", lang),
        "volatility_score": "Volatility Score" if lang == "en" else "Score de Volatilidade",
    },
)
fig_components.update_xaxes(tickformat=".1%")
fig_components.update_yaxes(tickformat=".1%")
st.plotly_chart(apply_chart_style(fig_components), width="stretch")

st.subheader(t("risk_scores_table", lang))
risk_table = compact_table(
    risk_scores,
    columns=[
        "strategy",
        "risk_score",
        "risk_profile",
        "max_drawdown",
        "avg_stake_pct_bankroll",
        "league_concentration",
        "max_red_streak",
    ],
    rename={
        "strategy": col_label("col_strategy", lang),
        "risk_score": col_label("col_risk_score", lang),
        "risk_profile": col_label("col_profile", lang),
        "max_drawdown": col_label("col_max_drawdown", lang),
        "avg_stake_pct_bankroll": col_label("col_avg_stake_pct", lang),
        "league_concentration": col_label("col_league_concentration", lang),
        "max_red_streak": col_label("col_max_red_streak", lang),
    },
    sort_by="risk_score",
    ascending=False,
    round_map={"risk_score": 1},
    pct_cols=["max_drawdown", "avg_stake_pct_bankroll", "league_concentration"],
    int_cols=["max_red_streak"],
    decimal_cols=["risk_score"],
    value_maps={"risk_profile": profile_map},
    lang=lang,
)
st.dataframe(risk_table, width="stretch", hide_index=True)

if not alerts.empty:
    st.subheader(t("risk_alerts_table", lang))
    alerts_table = alerts.copy()
    alerts_table["severity_order"] = alerts_table["severity"].map(SEVERITY_ORDER).fillna(99)
    alerts_table = alerts_table.sort_values(["severity_order", "strategy", "alert_type"])
    alerts_table["alert_type"] = alerts_table["alert_type"].astype(str).map(
        lambda value: ALERT_LABELS.get(lang, ALERT_LABELS["en"]).get(value, value)
    )
    alerts_table["severity"] = alerts_table["severity"].astype(str).map(
        lambda value: SEVERITY_LABELS.get(lang, SEVERITY_LABELS["en"]).get(value, value)
    )

    alerts_table = compact_table(
        alerts_table,
        columns=["strategy", "alert_type", "severity"],
        rename={
            "strategy": col_label("col_strategy", lang),
            "alert_type": col_label("col_alert", lang),
            "severity": col_label("col_severity", lang),
        },
        lang=lang,
    )
    st.dataframe(alerts_table, width="stretch", hide_index=True)
