from __future__ import annotations

from dataclasses import dataclass
from datetime import date
from pathlib import Path
from typing import Any

import pandas as pd
import plotly.graph_objects as go
import streamlit as st

BASE_DIR = Path(__file__).resolve().parents[1]
MARTS_DIR = BASE_DIR / "data" / "marts"

LANG_OPTIONS = {"English": "en", "Português": "pt"}

TEXT: dict[str, dict[str, str]] = {
    "en": {
        "missing_data_warning": "Marts not found. Run `python -m src.main seed` and `python -m src.main pipeline` first.",
        "sidebar_filters": "## Global Filters",
        "filter_strategies": "Strategies",
        "filter_leagues": "Leagues",
        "filter_markets": "Markets",
        "filter_methods": "Simulation Methods",
        "filter_date_range": "Date Range",
        "filter_caption": "Filters apply to matching columns on each page.",
        "kpi_total_bets": "Total Bets",
        "kpi_win_rate": "Win Rate",
        "kpi_yield": "Yield",
        "kpi_roi": "ROI",
        "kpi_avg_clv": "Avg CLV",
        "kpi_max_drawdown": "Max Drawdown",
        "home_title": "Sports Betting Intelligence Engine",
        "home_subtitle": "Analytics platform for performance quality, risk governance, and capital preservation.",
        "home_note": "Portfolio case focused on decision quality, volatility control, and transparent risk monitoring.",
        "home_info": "Analytical and educational project. Not financial or betting advice.",
        "home_workflow_title": "Analytics Workflow",
        "home_workflow_steps": "1. Ingest match and odds events into `raw`.\n2. Standardize records in `staging` with quality checks.\n3. Materialize KPI marts and risk layers.\n4. Compare scenarios in bankroll simulation.\n5. Expose insights in executive and exploratory dashboards.",
        "home_nav_title": "Navigation",
        "home_nav_items": "- **Overview:** KPI health and trend context.\n- **Strategies:** return vs risk profile analysis.\n- **Markets:** performance by market type.\n- **CLV:** execution quality diagnostics.\n- **Bankroll:** scenario and drawdown comparison.\n- **Risk:** governance score and alerts.\n- **Data Quality:** quality contract monitoring.",
        "home_monthly_title": "Monthly Performance Snapshot",
        "home_top_risk": "Highest Risk Exposure (Filtered)",
        "overview_title": "Overview",
        "overview_subtitle": "Top-line performance health and trend monitoring.",
        "overview_note": "Use this page to evaluate portfolio-level quality before strategy deep dives.",
        "overview_monthly_title": "Monthly Net Profit",
        "overview_net_by_league": "Net Profit by League",
        "overview_yield_by_market": "Yield by Market",
        "overview_league_rank": "League Ranking",
        "overview_market_rank": "Market Ranking",
        "strategies_title": "Strategy Analysis",
        "strategies_subtitle": "Return quality and risk posture by strategy.",
        "strategies_note": "A strong strategy combines edge, discipline, and stable drawdown.",
        "strategies_count": "Strategies",
        "strategies_filtered_pnl": "Filtered Net Profit",
        "strategies_avg_risk": "Avg Risk Score",
        "strategies_profit_risk": "Net Profit and Risk Profile by Strategy",
        "strategies_exec_quality": "Execution Quality vs Return Efficiency",
        "markets_title": "Market Analysis",
        "markets_subtitle": "Performance comparison across market families.",
        "markets_note": "Focus on the trade-off between return, hit rate, and drawdown.",
        "markets_count": "Markets",
        "markets_filtered_pnl": "Filtered Net Profit",
        "markets_avg_yield": "Avg Yield",
        "markets_net_by_market": "Net Profit by Market",
        "markets_odds_vs_yield": "Odds Level vs Yield by Market",
        "clv_title": "CLV Analysis",
        "clv_subtitle": "Captured odds vs closing line quality.",
        "clv_note": "Positive CLV over time suggests better entry timing and pricing discipline.",
        "clv_strategies": "Strategies",
        "clv_avg": "Avg CLV (Filtered)",
        "clv_net": "Net Profit (Filtered)",
        "clv_scatter": "Strategy CLV vs Yield",
        "clv_market": "Average CLV by Market",
        "clv_bookmaker_summary": "Bookmaker CLV Summary",
        "bankroll_title": "Bankroll Simulation",
        "bankroll_subtitle": "Capital trajectory under fixed, percentage, and fractional Kelly sizing.",
        "bankroll_note": "Use this view to compare return and drawdown trade-offs by sizing rule.",
        "bankroll_scenarios": "Scenarios",
        "bankroll_best_method": "Best Method",
        "bankroll_best_roi": "Best ROI",
        "bankroll_curve": "Bankroll Evolution by Scenario",
        "bankroll_drawdown": "Drawdown Trajectory by Scenario",
        "risk_title": "Risk Governance Panel",
        "risk_subtitle": "Risk score, concentration, and governance signals.",
        "risk_note": "This layer exists to prioritize capital preservation and decision discipline.",
        "risk_assessed": "Strategies Assessed",
        "risk_avg_score": "Avg Risk Score",
        "risk_high_risk": "High Risk Strategies",
        "risk_score_by_strategy": "Risk Score by Strategy",
        "risk_drawdown_vs_stake": "Drawdown vs Stake Intensity",
        "risk_scores_table": "Risk Scores",
        "risk_alerts_table": "Risk Alerts",
        "dq_title": "Data Quality Dashboard",
        "dq_subtitle": "Validation status across critical and warning checks.",
        "dq_note": "Quality gates protect metric credibility before interpretation.",
        "dq_total_checks": "Total Checks",
        "dq_failed_checks": "Failed Checks",
        "dq_critical_fails": "Critical Fails",
        "dq_chart": "Validation Checks by Severity and Status",
        "col_strategy": "Strategy",
        "col_league": "League",
        "col_market": "Market",
        "col_bookmaker": "Bookmaker",
        "col_method": "Method",
        "col_bets": "Bets",
        "col_net_pnl": "Net P&L",
        "col_yield": "Yield",
        "col_win_rate": "Win Rate",
        "col_avg_clv": "Avg CLV",
        "col_max_drawdown": "Max Drawdown",
        "col_risk_score": "Risk Score",
        "col_profile": "Profile",
        "col_final_bankroll": "Final Bankroll",
        "col_roi": "ROI",
        "col_executed_bets": "Executed Bets",
        "col_skipped_bets": "Skipped Bets",
        "col_avg_stake_pct": "Avg Stake %",
        "col_league_concentration": "League Concentration",
        "col_max_red_streak": "Max Red Streak",
        "col_alert": "Alert",
        "col_severity": "Severity",
        "col_check": "Check",
        "col_status": "Status",
        "col_failed_rows": "Failed Rows",
        "col_details": "Details",
    },
    "pt": {
        "missing_data_warning": "Marts não encontrados. Execute `python -m src.main seed` e `python -m src.main pipeline` primeiro.",
        "sidebar_filters": "## Filtros Globais",
        "filter_strategies": "Estratégias",
        "filter_leagues": "Ligas",
        "filter_markets": "Mercados",
        "filter_methods": "Métodos de Simulação",
        "filter_date_range": "Período",
        "filter_caption": "Os filtros são aplicados às colunas compatíveis em cada página.",
        "kpi_total_bets": "Total de Apostas",
        "kpi_win_rate": "Taxa de Acerto",
        "kpi_yield": "Yield",
        "kpi_roi": "ROI",
        "kpi_avg_clv": "CLV Médio",
        "kpi_max_drawdown": "Drawdown Máximo",
        "home_title": "Sports Betting Intelligence Engine",
        "home_subtitle": "Plataforma analítica para qualidade de performance, governança de risco e preservação de capital.",
        "home_note": "Case de portfólio com foco em decisão orientada por dados, controle de volatilidade e monitoramento de risco.",
        "home_info": "Projeto para fins analíticos e educacionais. Não é recomendação financeira ou de aposta.",
        "home_workflow_title": "Fluxo Analítico",
        "home_workflow_steps": "1. Ingestão de eventos de partidas e odds na camada `raw`.\n2. Padronização na camada `staging` com verificações de qualidade.\n3. Materialização de KPIs e camadas de risco.\n4. Comparação de cenários no simulador de banca.\n5. Exposição de insights em painéis executivos e exploratórios.",
        "home_nav_title": "Navegação",
        "home_nav_items": "- **Overview:** saúde dos KPIs e tendência.\n- **Strategies:** retorno vs perfil de risco.\n- **Markets:** performance por tipo de mercado.\n- **CLV:** qualidade de execução.\n- **Bankroll:** cenários e drawdown.\n- **Risk:** score e alertas de governança.\n- **Data Quality:** monitoramento de qualidade dos dados.",
        "home_monthly_title": "Resumo Mensal de Performance",
        "home_top_risk": "Maior Exposição de Risco (Filtro Atual)",
        "overview_title": "Visão Geral",
        "overview_subtitle": "Saúde da performance e tendência no nível executivo.",
        "overview_note": "Use esta página para avaliar a qualidade do portfólio antes do detalhamento por estratégia.",
        "overview_monthly_title": "Lucro Líquido Mensal",
        "overview_net_by_league": "Lucro Líquido por Liga",
        "overview_yield_by_market": "Yield por Mercado",
        "overview_league_rank": "Ranking de Ligas",
        "overview_market_rank": "Ranking de Mercados",
        "strategies_title": "Análise de Estratégias",
        "strategies_subtitle": "Qualidade de retorno e postura de risco por estratégia.",
        "strategies_note": "Uma estratégia forte combina edge, disciplina e drawdown controlado.",
        "strategies_count": "Estratégias",
        "strategies_filtered_pnl": "Lucro Líquido (Filtro)",
        "strategies_avg_risk": "Score Médio de Risco",
        "strategies_profit_risk": "Lucro Líquido e Perfil de Risco por Estratégia",
        "strategies_exec_quality": "Qualidade de Execução vs Eficiência de Retorno",
        "markets_title": "Análise de Mercados",
        "markets_subtitle": "Comparação de performance entre famílias de mercado.",
        "markets_note": "Foco no trade-off entre retorno, acerto e drawdown.",
        "markets_count": "Mercados",
        "markets_filtered_pnl": "Lucro Líquido (Filtro)",
        "markets_avg_yield": "Yield Médio",
        "markets_net_by_market": "Lucro Líquido por Mercado",
        "markets_odds_vs_yield": "Nível de Odds vs Yield por Mercado",
        "clv_title": "Análise de CLV",
        "clv_subtitle": "Qualidade das odds capturadas frente à linha de fechamento.",
        "clv_note": "CLV positivo consistente costuma indicar melhor timing e disciplina de entrada.",
        "clv_strategies": "Estratégias",
        "clv_avg": "CLV Médio (Filtro)",
        "clv_net": "Lucro Líquido (Filtro)",
        "clv_scatter": "CLV vs Yield por Estratégia",
        "clv_market": "CLV Médio por Mercado",
        "clv_bookmaker_summary": "Resumo de CLV por Bookmaker",
        "bankroll_title": "Simulação de Banca",
        "bankroll_subtitle": "Trajetória de capital em stake fixa, percentual e Kelly fracionado.",
        "bankroll_note": "Use esta visão para comparar retorno e drawdown entre regras de stake.",
        "bankroll_scenarios": "Cenários",
        "bankroll_best_method": "Melhor Método",
        "bankroll_best_roi": "Melhor ROI",
        "bankroll_curve": "Evolução da Banca por Cenário",
        "bankroll_drawdown": "Trajetória de Drawdown por Cenário",
        "risk_title": "Painel de Governança de Risco",
        "risk_subtitle": "Score de risco, concentração e sinais de governança.",
        "risk_note": "Esta camada existe para priorizar preservação de capital e disciplina operacional.",
        "risk_assessed": "Estratégias Avaliadas",
        "risk_avg_score": "Score Médio de Risco",
        "risk_high_risk": "Estratégias de Alto Risco",
        "risk_score_by_strategy": "Score de Risco por Estratégia",
        "risk_drawdown_vs_stake": "Drawdown vs Intensidade de Stake",
        "risk_scores_table": "Scores de Risco",
        "risk_alerts_table": "Alertas de Risco",
        "dq_title": "Painel de Qualidade de Dados",
        "dq_subtitle": "Status de validação entre checagens críticas e de alerta.",
        "dq_note": "Gates de qualidade protegem a credibilidade dos indicadores.",
        "dq_total_checks": "Total de Checagens",
        "dq_failed_checks": "Checagens com Falha",
        "dq_critical_fails": "Falhas Críticas",
        "dq_chart": "Checagens por Severidade e Status",
        "col_strategy": "Estratégia",
        "col_league": "Liga",
        "col_market": "Mercado",
        "col_bookmaker": "Bookmaker",
        "col_method": "Método",
        "col_bets": "Apostas",
        "col_net_pnl": "Lucro Líquido",
        "col_yield": "Yield",
        "col_win_rate": "Taxa de Acerto",
        "col_avg_clv": "CLV Médio",
        "col_max_drawdown": "Drawdown Máximo",
        "col_risk_score": "Score de Risco",
        "col_profile": "Perfil",
        "col_final_bankroll": "Banca Final",
        "col_roi": "ROI",
        "col_executed_bets": "Apostas Executadas",
        "col_skipped_bets": "Apostas Puladas",
        "col_avg_stake_pct": "Stake Média %",
        "col_league_concentration": "Concentração em Liga",
        "col_max_red_streak": "Máx. Sequência de Reds",
        "col_alert": "Alerta",
        "col_severity": "Severidade",
        "col_check": "Checagem",
        "col_status": "Status",
        "col_failed_rows": "Linhas com Falha",
        "col_details": "Detalhes",
    },
}

MARKET_LABELS = {
    "en": {
        "MONEYLINE_HOME": "Home Win",
        "OVER_2_5": "Over 2.5",
        "BTTS_YES": "BTTS Yes",
        "DNB_HOME": "Home DNB",
    },
    "pt": {
        "MONEYLINE_HOME": "Vitória Casa",
        "OVER_2_5": "Mais de 2.5",
        "BTTS_YES": "Ambas Marcam",
        "DNB_HOME": "Casa DNB",
    },
}

ALERT_LABELS = {
    "en": {
        "drawdown_limit_breach": "Drawdown Limit Breach",
        "elevated_volatility": "Elevated Volatility",
        "league_concentration": "League Concentration",
        "long_loss_streak": "Long Loss Streak",
        "no_critical_alerts": "No Critical Alerts",
    },
    "pt": {
        "drawdown_limit_breach": "Estouro de Limite de Drawdown",
        "elevated_volatility": "Volatilidade Elevada",
        "league_concentration": "Concentração em Liga",
        "long_loss_streak": "Sequência Longa de Reds",
        "no_critical_alerts": "Sem Alertas Críticos",
    },
}

PROFILE_LABELS = {
    "en": {"Conservative": "Conservative", "Moderate": "Moderate", "Aggressive": "Aggressive"},
    "pt": {"Conservative": "Conservadora", "Moderate": "Moderada", "Aggressive": "Agressiva"},
}

SEVERITY_LABELS = {
    "en": {"high": "High", "medium": "Medium", "info": "Info"},
    "pt": {"high": "Alta", "medium": "Média", "info": "Info"},
}

SEVERITY_ORDER = {"high": 0, "medium": 1, "info": 2}


def t(key: str, lang: str = "en") -> str:
    fallback = TEXT["en"].get(key, key)
    return TEXT.get(lang, TEXT["en"]).get(key, fallback)


def col_label(key: str, lang: str = "en") -> str:
    return t(key, lang)


def _localize_number(token: str, lang: str) -> str:
    if lang != "pt":
        return token
    return token.replace(",", "§").replace(".", ",").replace("§", ".")


def format_number(value: Any, lang: str = "en", decimals: int = 2) -> str:
    if pd.isna(value):
        return "-"
    return _localize_number(f"{float(value):,.{decimals}f}", lang)


def format_int(value: Any, lang: str = "en") -> str:
    if pd.isna(value):
        return "-"
    return _localize_number(f"{int(round(float(value))):,}", lang)


def format_pct(value: Any, lang: str = "en", decimals: int = 2) -> str:
    if pd.isna(value):
        return "-"
    pct_value = float(value) * 100
    return f"{format_number(pct_value, lang, decimals)}%"


def to_market_label(value: str, lang: str = "en") -> str:
    return MARKET_LABELS.get(lang, MARKET_LABELS["en"]).get(str(value), str(value))


def to_alert_label(value: str, lang: str = "en") -> str:
    return ALERT_LABELS.get(lang, ALERT_LABELS["en"]).get(str(value), str(value))


def to_profile_label(value: str, lang: str = "en") -> str:
    return PROFILE_LABELS.get(lang, PROFILE_LABELS["en"]).get(str(value), str(value))


def to_severity_label(value: str, lang: str = "en") -> str:
    return SEVERITY_LABELS.get(lang, SEVERITY_LABELS["en"]).get(str(value), str(value))


@st.cache_data(show_spinner=False)
def load_mart(table_name: str) -> pd.DataFrame:
    path = MARTS_DIR / f"{table_name}.csv"
    if not path.exists():
        return pd.DataFrame()
    return pd.read_csv(path)


def show_missing_data_message(lang: str = "en") -> None:
    st.warning(t("missing_data_warning", lang))


@dataclass(frozen=True)
class GlobalFilters:
    strategies: list[str]
    leagues: list[str]
    markets: list[str]
    methods: list[str]
    start_date: date | None
    end_date: date | None
    lang: str


def inject_styles() -> None:
    st.markdown(
        """
<style>
.block-container {
    max-width: 1380px;
    padding-top: 1.8rem;
    padding-bottom: 2rem;
}
.hero-title {
    font-size: 1.85rem;
    font-weight: 700;
    margin-bottom: 0.12rem;
}
.hero-subtitle {
    color: #4b5563;
    margin-bottom: 0.75rem;
}
.section-note {
    color: #6b7280;
    font-size: 0.92rem;
    margin-top: -0.15rem;
    margin-bottom: 0.75rem;
}
[data-testid="stMetric"] {
    background: #f8fafc;
    border: 1px solid #e5e7eb;
    border-radius: 10px;
    padding: 0.55rem 0.65rem;
}
[data-testid="stMetricLabel"] p {
    font-size: 0.84rem;
}
[data-testid="stMetricValue"] {
    font-size: 1.30rem;
}
div[data-testid="stDataFrame"] {
    border: 1px solid #e5e7eb;
    border-radius: 10px;
}
</style>
""",
        unsafe_allow_html=True,
    )


def render_page_header(title: str, subtitle: str) -> None:
    st.markdown(f"<div class='hero-title'>{title}</div>", unsafe_allow_html=True)
    st.markdown(f"<div class='hero-subtitle'>{subtitle}</div>", unsafe_allow_html=True)


def render_section_note(note: str) -> None:
    st.markdown(f"<div class='section-note'>{note}</div>", unsafe_allow_html=True)


def apply_chart_style(fig: go.Figure) -> go.Figure:
    fig.update_layout(
        template="plotly_white",
        margin=dict(l=16, r=16, t=56, b=12),
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="left", x=0),
    )
    fig.update_xaxes(showgrid=False)
    fig.update_yaxes(showgrid=True, gridcolor="#e5e7eb")
    return fig


def render_kpi_strip(overall_df: pd.DataFrame, lang: str = "en") -> None:
    if overall_df.empty:
        return
    row = overall_df.iloc[0]
    c1, c2, c3, c4, c5, c6 = st.columns(6)
    c1.metric(t("kpi_total_bets", lang), format_int(row["total_bets"], lang))
    c2.metric(t("kpi_win_rate", lang), format_pct(row["win_rate"], lang))
    c3.metric(t("kpi_yield", lang), format_pct(row["yield_pct"], lang))
    c4.metric(t("kpi_roi", lang), format_pct(row["roi"], lang))
    c5.metric(t("kpi_avg_clv", lang), format_pct(row["avg_clv"], lang))
    c6.metric(t("kpi_max_drawdown", lang), format_pct(row["max_drawdown"], lang))


def _extract_date_range() -> tuple[date | None, date | None]:
    bankroll_df = load_mart("fact_bankroll_evolution")
    if bankroll_df.empty or "settled_date" not in bankroll_df.columns:
        return None, None
    series = pd.to_datetime(bankroll_df["settled_date"], errors="coerce").dropna()
    if series.empty:
        return None, None
    return series.min().date(), series.max().date()


def _options(df: pd.DataFrame, column: str) -> list[str]:
    if column not in df.columns:
        return []
    return sorted(df[column].dropna().astype(str).unique().tolist())


def build_global_filters() -> GlobalFilters:
    strategy_df = load_mart("mart_strategy_performance")
    league_df = load_mart("mart_league_performance")
    market_df = load_mart("mart_market_performance")
    scenario_df = load_mart("mart_bankroll_scenarios_summary")
    min_date, max_date = _extract_date_range()

    language_label = st.sidebar.selectbox(
        "Language / Idioma",
        options=list(LANG_OPTIONS.keys()),
        key="global_language",
    )
    lang = LANG_OPTIONS.get(language_label, "en")

    strategy_options = _options(strategy_df, "strategy")
    league_options = _options(league_df, "league")
    market_options = _options(market_df, "market")
    method_options = _options(scenario_df, "method")
    market_label_to_code = {to_market_label(code, lang): code for code in market_options}
    market_label_options = list(market_label_to_code.keys())

    st.sidebar.markdown(t("sidebar_filters", lang))
    strategies = st.sidebar.multiselect(
        t("filter_strategies", lang),
        options=strategy_options,
        default=strategy_options,
        key="global_strategies",
    )
    leagues = st.sidebar.multiselect(
        t("filter_leagues", lang),
        options=league_options,
        default=league_options,
        key="global_leagues",
    )
    selected_market_labels = st.sidebar.multiselect(
        t("filter_markets", lang),
        options=market_label_options,
        default=market_label_options,
        key="global_markets",
    )
    markets = [market_label_to_code[label] for label in selected_market_labels]
    methods = st.sidebar.multiselect(
        t("filter_methods", lang),
        options=method_options,
        default=method_options,
        key="global_methods",
    )

    if min_date and max_date:
        date_range = st.sidebar.date_input(
            t("filter_date_range", lang),
            value=(min_date, max_date),
            min_value=min_date,
            max_value=max_date,
            key="global_date_range",
        )
        if isinstance(date_range, tuple) and len(date_range) == 2:
            start_date, end_date = date_range
        else:
            start_date, end_date = min_date, max_date
    else:
        start_date, end_date = None, None

    st.sidebar.caption(t("filter_caption", lang))
    return GlobalFilters(
        strategies=strategies,
        leagues=leagues,
        markets=markets,
        methods=methods,
        start_date=start_date,
        end_date=end_date,
        lang=lang,
    )


def _filter_by_date(df: pd.DataFrame, filters: GlobalFilters) -> pd.DataFrame:
    if filters.start_date is None or filters.end_date is None:
        return df

    if "month" in df.columns:
        out = df.copy()
        month_dates = pd.to_datetime(out["month"].astype(str) + "-01", errors="coerce").dt.date
        mask = (month_dates >= filters.start_date) & (month_dates <= filters.end_date)
        return out.loc[mask].reset_index(drop=True)

    date_cols = ["settled_date", "placed_date", "date", "placed_ts", "snapshot_ts"]
    for col in date_cols:
        if col in df.columns:
            out = df.copy()
            parsed = pd.to_datetime(out[col], errors="coerce").dt.date
            mask = (parsed >= filters.start_date) & (parsed <= filters.end_date)
            return out.loc[mask].reset_index(drop=True)
    return df


def apply_global_filters(df: pd.DataFrame, filters: GlobalFilters) -> pd.DataFrame:
    if df.empty:
        return df
    out = df.copy()
    if "strategy" in out.columns and filters.strategies:
        out = out[out["strategy"].astype(str).isin(filters.strategies)]
    if "league" in out.columns and filters.leagues:
        out = out[out["league"].astype(str).isin(filters.leagues)]
    if "market" in out.columns and filters.markets:
        out = out[out["market"].astype(str).isin(filters.markets)]
    if "method" in out.columns and filters.methods:
        out = out[out["method"].astype(str).isin(filters.methods)]
    out = _filter_by_date(out, filters)
    return out.reset_index(drop=True)


def apply_market_labels(df: pd.DataFrame, lang: str = "en", column: str = "market") -> pd.DataFrame:
    if df.empty or column not in df.columns:
        return df
    out = df.copy()
    out[column] = out[column].map(lambda value: to_market_label(str(value), lang))
    return out


def compact_table(
    df: pd.DataFrame,
    columns: list[str],
    *,
    rename: dict[str, str] | None = None,
    sort_by: str | None = None,
    ascending: bool = False,
    top_n: int | None = None,
    lang: str = "en",
    round_map: dict[str, int] | None = None,
    pct_cols: list[str] | None = None,
    int_cols: list[str] | None = None,
    decimal_cols: list[str] | None = None,
    value_maps: dict[str, dict[str, str]] | None = None,
) -> pd.DataFrame:
    if df.empty:
        return df

    out = df.copy()
    if sort_by and sort_by in out.columns:
        out = out.sort_values(sort_by, ascending=ascending, na_position="last")
    if top_n:
        out = out.head(top_n)

    selected = [col for col in columns if col in out.columns]
    out = out[selected].copy()

    for col, mapping in (value_maps or {}).items():
        if col in out.columns:
            out[col] = out[col].astype(str).map(lambda value, m=mapping: m.get(value, value))

    def precision(col: str, default: int) -> int:
        if not round_map:
            return default
        return int(round_map.get(col, default))

    for col in pct_cols or []:
        if col in out.columns:
            digits = precision(col, 2)
            values = pd.to_numeric(out[col], errors="coerce")
            out[col] = values.map(lambda value, d=digits: format_pct(value, lang, d))

    for col in int_cols or []:
        if col in out.columns:
            values = pd.to_numeric(out[col], errors="coerce")
            out[col] = values.map(lambda value: format_int(value, lang))

    for col in decimal_cols or []:
        if col in out.columns:
            digits = precision(col, 2)
            values = pd.to_numeric(out[col], errors="coerce")
            out[col] = values.map(lambda value, d=digits: format_number(value, lang, d))

    if rename:
        out = out.rename(columns=rename)

    return out.reset_index(drop=True)
