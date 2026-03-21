from __future__ import annotations

import numpy as np
import pandas as pd

EMPTY_METRICS: dict[str, float | int] = {
    "total_bets": 0,
    "settled_bets": 0,
    "win_rate": 0.0,
    "loss_rate": 0.0,
    "push_rate": 0.0,
    "net_profit": 0.0,
    "total_stake": 0.0,
    "roi": 0.0,
    "yield_pct": 0.0,
    "avg_stake": 0.0,
    "avg_odds": 0.0,
    "profit_factor": 0.0,
    "expectancy": 0.0,
    "avg_clv": 0.0,
    "max_drawdown": 0.0,
    "max_green_streak": 0,
    "max_red_streak": 0,
    "bankroll_volatility": 0.0,
    "sharpe_like": 0.0,
}


def calculate_drawdown(equity_curve: pd.Series) -> float:
    if equity_curve.empty:
        return 0.0
    running_peak = equity_curve.cummax()
    drawdown = (equity_curve / running_peak) - 1.0
    return float(abs(drawdown.min()))


def calculate_streaks(results: pd.Series) -> tuple[int, int]:
    max_wins = 0
    max_losses = 0
    current_wins = 0
    current_losses = 0

    for result in results.fillna(""):
        if result == "win":
            current_wins += 1
            current_losses = 0
        elif result == "loss":
            current_losses += 1
            current_wins = 0
        else:
            current_wins = 0
            current_losses = 0
        max_wins = max(max_wins, current_wins)
        max_losses = max(max_losses, current_losses)

    return max_wins, max_losses


def calculate_sharpe_like(daily_returns: pd.Series) -> float:
    if daily_returns.empty:
        return 0.0
    std = float(daily_returns.std(ddof=0))
    if std == 0:
        return 0.0
    return float((daily_returns.mean() / std) * np.sqrt(252))


def compute_bankroll_curve(
    bets_df: pd.DataFrame, initial_bankroll: float = 10_000.0
) -> pd.DataFrame:
    if bets_df.empty:
        return pd.DataFrame(columns=["settled_date", "daily_pnl", "bankroll", "drawdown"])

    daily = (
        bets_df.assign(settled_date=pd.to_datetime(bets_df["settled_ts"]).dt.date)
        .groupby("settled_date", as_index=False)["pnl"]
        .sum()
        .rename(columns={"pnl": "daily_pnl"})
        .sort_values("settled_date")
    )
    daily["bankroll"] = initial_bankroll + daily["daily_pnl"].cumsum()
    peak = daily["bankroll"].cummax()
    daily["drawdown"] = (daily["bankroll"] / peak) - 1.0
    return daily


def calculate_core_metrics(
    bets_df: pd.DataFrame, initial_bankroll: float = 10_000.0
) -> dict[str, float | int]:
    if bets_df.empty:
        return EMPTY_METRICS.copy()

    bets = bets_df.copy()
    bets["result"] = bets["result"].astype(str).str.lower().str.strip()
    total_bets = int(len(bets))
    settled_bets = int(bets["result"].isin(["win", "loss", "push"]).sum())

    wins = int((bets["result"] == "win").sum())
    losses = int((bets["result"] == "loss").sum())
    pushes = int((bets["result"] == "push").sum())

    settled_denominator = settled_bets if settled_bets else 1
    win_rate = wins / settled_denominator
    loss_rate = losses / settled_denominator
    push_rate = pushes / settled_denominator

    total_stake = float(bets["stake"].sum())
    net_profit = float(bets["pnl"].sum())
    roi = float(net_profit / initial_bankroll) if initial_bankroll else 0.0
    yield_pct = float(net_profit / total_stake) if total_stake else 0.0

    avg_stake = float(bets["stake"].mean()) if total_bets else 0.0
    avg_odds = float(bets["captured_odds"].mean()) if total_bets else 0.0
    avg_clv = float(bets["clv"].mean()) if "clv" in bets.columns and total_bets else 0.0

    gross_wins = float(bets.loc[bets["pnl"] > 0, "pnl"].sum())
    gross_losses = abs(float(bets.loc[bets["pnl"] < 0, "pnl"].sum()))
    profit_factor = float(gross_wins / gross_losses) if gross_losses else float("inf")

    avg_win = float(bets.loc[bets["pnl"] > 0, "pnl"].mean()) if wins else 0.0
    avg_loss = abs(float(bets.loc[bets["pnl"] < 0, "pnl"].mean())) if losses else 0.0
    decision_bets = wins + losses
    win_prob = wins / decision_bets if decision_bets else 0.0
    loss_prob = losses / decision_bets if decision_bets else 0.0
    expectancy = float(win_prob * avg_win - loss_prob * avg_loss)

    bankroll_curve = compute_bankroll_curve(bets, initial_bankroll=initial_bankroll)
    max_drawdown = (
        calculate_drawdown(bankroll_curve["bankroll"]) if not bankroll_curve.empty else 0.0
    )

    max_green_streak, max_red_streak = calculate_streaks(bets["result"])
    daily_returns = (
        bankroll_curve["daily_pnl"] / initial_bankroll
        if not bankroll_curve.empty
        else pd.Series(dtype=float)
    )
    bankroll_volatility = (
        float(daily_returns.std(ddof=0) * np.sqrt(252)) if not daily_returns.empty else 0.0
    )
    sharpe_like = calculate_sharpe_like(daily_returns)

    return {
        "total_bets": total_bets,
        "settled_bets": settled_bets,
        "win_rate": round(win_rate, 4),
        "loss_rate": round(loss_rate, 4),
        "push_rate": round(push_rate, 4),
        "net_profit": round(net_profit, 2),
        "total_stake": round(total_stake, 2),
        "roi": round(roi, 4),
        "yield_pct": round(yield_pct, 4),
        "avg_stake": round(avg_stake, 2),
        "avg_odds": round(avg_odds, 4),
        "profit_factor": round(profit_factor, 4) if np.isfinite(profit_factor) else float("inf"),
        "expectancy": round(expectancy, 4),
        "avg_clv": round(avg_clv, 4),
        "max_drawdown": round(max_drawdown, 4),
        "max_green_streak": max_green_streak,
        "max_red_streak": max_red_streak,
        "bankroll_volatility": round(bankroll_volatility, 4),
        "sharpe_like": round(sharpe_like, 4),
    }


def performance_by_dimension(
    bets_df: pd.DataFrame, group_col: str, initial_bankroll: float = 10_000.0
) -> pd.DataFrame:
    if bets_df.empty:
        return pd.DataFrame(columns=[group_col, *EMPTY_METRICS.keys()])

    rows = []
    for key, frame in bets_df.groupby(group_col):
        metrics = calculate_core_metrics(frame, initial_bankroll=initial_bankroll)
        row = {group_col: key, **metrics}
        rows.append(row)
    result = pd.DataFrame(rows).sort_values("net_profit", ascending=False).reset_index(drop=True)
    return result


def monthly_performance(bets_df: pd.DataFrame) -> pd.DataFrame:
    if bets_df.empty:
        return pd.DataFrame(columns=["month", "bets", "stake", "pnl", "yield_pct", "avg_clv"])

    monthly = bets_df.copy()
    monthly["month"] = pd.to_datetime(monthly["settled_ts"]).dt.to_period("M").astype(str)
    grouped = (
        monthly.groupby("month", as_index=False)
        .agg(
            bets=("bet_id", "count"),
            stake=("stake", "sum"),
            pnl=("pnl", "sum"),
            avg_clv=("clv", "mean"),
        )
        .sort_values("month")
    )
    grouped["yield_pct"] = grouped["pnl"] / grouped["stake"].replace(0, np.nan)
    grouped["yield_pct"] = grouped["yield_pct"].fillna(0.0)
    return grouped
