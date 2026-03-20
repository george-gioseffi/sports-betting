from __future__ import annotations

import numpy as np
import pandas as pd

from src.analytics.metrics_calculator import calculate_core_metrics
from src.config.settings import RISK_LIMITS

RISK_COLUMNS = [
    "strategy",
    "risk_score",
    "risk_profile",
    "avg_stake_pct_bankroll",
    "max_drawdown",
    "max_red_streak",
    "avg_clv",
    "league_concentration",
    "volatility_score",
    "drawdown_score",
    "stake_score",
    "concentration_score",
    "clv_score",
    "streak_score",
]

ALERT_COLUMNS = ["strategy", "alert_type", "severity"]


def _clip01(value: float) -> float:
    return float(np.clip(value, 0.0, 1.0))


def _classify_profile(score: float) -> str:
    if score <= 33:
        return "Conservative"
    if score <= 66:
        return "Moderate"
    return "Aggressive"


def _strategy_alerts(row: dict[str, float | int | str]) -> list[str]:
    alerts = []
    if row["max_drawdown"] > RISK_LIMITS["max_drawdown_threshold"]:
        alerts.append("drawdown_limit_breach")
    if row["volatility_score"] > 0.7:
        alerts.append("elevated_volatility")
    if row["league_concentration"] > 0.45:
        alerts.append("league_concentration")
    if row["max_red_streak"] >= 8:
        alerts.append("long_loss_streak")
    return alerts


def compute_risk_scores(
    bets_df: pd.DataFrame, initial_bankroll: float = 10_000.0
) -> tuple[pd.DataFrame, pd.DataFrame]:
    if bets_df.empty:
        return pd.DataFrame(columns=RISK_COLUMNS), pd.DataFrame(columns=ALERT_COLUMNS)

    rows: list[dict] = []
    for strategy, frame in bets_df.groupby("strategy"):
        metrics = calculate_core_metrics(frame, initial_bankroll=initial_bankroll)
        stake_pct = float(frame["stake"].mean() / initial_bankroll) if initial_bankroll else 0.0
        daily_pnl = (
            frame.assign(day=pd.to_datetime(frame["settled_ts"]).dt.date)
            .groupby("day")["pnl"]
            .sum()
        )
        volatility = float(daily_pnl.std(ddof=0) / initial_bankroll) if not daily_pnl.empty else 0.0
        league_shares = frame["league"].value_counts(normalize=True)
        league_concentration = float(league_shares.max()) if not league_shares.empty else 0.0
        clv_penalty = max(0.0, -float(metrics["avg_clv"]))

        volatility_score = _clip01(volatility / 0.04)
        drawdown_score = _clip01(float(metrics["max_drawdown"]) / 0.25)
        stake_score = _clip01(stake_pct / 0.02)
        concentration_score = _clip01(league_concentration / 0.55)
        clv_score = _clip01(clv_penalty / 0.02)
        streak_score = _clip01(float(metrics["max_red_streak"]) / 12)

        raw_score = 100 * (
            0.24 * volatility_score
            + 0.22 * drawdown_score
            + 0.16 * stake_score
            + 0.16 * concentration_score
            + 0.12 * clv_score
            + 0.10 * streak_score
        )
        risk_score = round(float(np.clip(raw_score, 0.0, 100.0)), 2)

        rows.append(
            {
                "strategy": strategy,
                "risk_score": risk_score,
                "risk_profile": _classify_profile(risk_score),
                "avg_stake_pct_bankroll": round(stake_pct, 4),
                "max_drawdown": float(metrics["max_drawdown"]),
                "max_red_streak": int(metrics["max_red_streak"]),
                "avg_clv": float(metrics["avg_clv"]),
                "league_concentration": round(league_concentration, 4),
                "volatility_score": round(volatility_score, 4),
                "drawdown_score": round(drawdown_score, 4),
                "stake_score": round(stake_score, 4),
                "concentration_score": round(concentration_score, 4),
                "clv_score": round(clv_score, 4),
                "streak_score": round(streak_score, 4),
            }
        )

    if not rows:
        return pd.DataFrame(columns=RISK_COLUMNS), pd.DataFrame(columns=ALERT_COLUMNS)

    risk_df = pd.DataFrame(rows).sort_values("risk_score", ascending=False).reset_index(drop=True)
    alerts_rows: list[dict[str, str]] = []
    for item in risk_df.to_dict("records"):
        alerts = _strategy_alerts(item)
        if not alerts:
            alerts_rows.append(
                {"strategy": item["strategy"], "alert_type": "no_critical_alerts", "severity": "info"}
            )
        for alert in alerts:
            severity = "high" if alert in {"drawdown_limit_breach", "elevated_volatility"} else "medium"
            alerts_rows.append({"strategy": item["strategy"], "alert_type": alert, "severity": severity})

    if not alerts_rows:
        return risk_df, pd.DataFrame(columns=ALERT_COLUMNS)

    alerts_df = pd.DataFrame(alerts_rows).sort_values(["severity", "strategy"]).reset_index(drop=True)
    return risk_df, alerts_df
