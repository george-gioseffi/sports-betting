from __future__ import annotations

from dataclasses import dataclass

import numpy as np
import pandas as pd

from src.analytics.metrics_calculator import calculate_drawdown


@dataclass
class SimulationConfig:
    method: str
    initial_bankroll: float = 10_000.0
    fixed_stake: float = 100.0
    pct_stake: float = 0.015
    kelly_fraction: float = 0.5
    daily_loss_limit: float = 0.08
    max_exposure_market: float = 0.12
    max_exposure_league: float = 0.25
    max_exposure_bookmaker: float = 0.18


def _estimate_probability(captured_odds: float, closing_odds: float) -> float:
    implied_prob = 1.0 / max(1.01, closing_odds)
    edge = (captured_odds / max(1.01, closing_odds)) - 1.0
    adjusted_prob = implied_prob * (1.0 + edge * 0.8)
    return float(np.clip(adjusted_prob, 0.02, 0.98))


def _kelly_stake_fraction(odds: float, probability: float) -> float:
    b = max(odds - 1.0, 0.01)
    q = 1.0 - probability
    raw = ((b * probability) - q) / b
    return float(np.clip(raw, 0.0, 0.1))


def _pnl_for_result(result: str, odds: float, stake: float) -> float:
    if result == "win":
        return round(stake * (odds - 1.0), 2)
    if result == "push":
        return 0.0
    return round(-stake, 2)


def _planned_stake(row: pd.Series, bankroll: float, config: SimulationConfig) -> float:
    if config.method == "fixed":
        return float(config.fixed_stake)
    if config.method == "percentage":
        return float(bankroll * config.pct_stake)
    if config.method == "kelly":
        prob = _estimate_probability(row["captured_odds"], row["closing_odds"])
        kelly_pct = _kelly_stake_fraction(row["captured_odds"], prob) * config.kelly_fraction
        return float(bankroll * kelly_pct)
    raise ValueError(f"Unsupported simulation method: {config.method}")


def simulate_bankroll(bets_df: pd.DataFrame, config: SimulationConfig) -> pd.DataFrame:
    bets = bets_df.copy().sort_values(["placed_ts", "bet_id"]).reset_index(drop=True)
    bankroll = config.initial_bankroll
    daily_realized_pnl: dict[str, float] = {}
    market_exposure: dict[tuple[str, str], float] = {}
    league_exposure: dict[tuple[str, str], float] = {}
    bookmaker_exposure: dict[tuple[str, str], float] = {}

    rows: list[dict] = []

    for _, row in bets.iterrows():
        bet_date = str(pd.to_datetime(row["placed_ts"]).date())
        key_market = (bet_date, str(row["market"]))
        key_league = (bet_date, str(row["league"]))
        key_bookmaker = (bet_date, str(row["bookmaker"]))
        current_day_loss = daily_realized_pnl.get(bet_date, 0.0)

        if current_day_loss <= -(config.initial_bankroll * config.daily_loss_limit):
            rows.append(
                {
                    "bet_id": row["bet_id"],
                    "method": config.method,
                    "placed_ts": row["placed_ts"],
                    "bankroll_before": bankroll,
                    "planned_stake": 0.0,
                    "executed_stake": 0.0,
                    "pnl": 0.0,
                    "result": "skipped",
                    "skip_reason": "daily_loss_limit",
                    "bankroll_after": bankroll,
                    "league": row["league"],
                    "market": row["market"],
                    "strategy": row["strategy"],
                }
            )
            continue

        planned_stake = max(0.0, _planned_stake(row, bankroll, config))
        executed_stake = min(planned_stake, bankroll)
        skip_reason = ""

        breaches = [
            (
                "market_exposure_limit",
                market_exposure.get(key_market, 0.0) + executed_stake > bankroll * config.max_exposure_market,
            ),
            (
                "league_exposure_limit",
                league_exposure.get(key_league, 0.0) + executed_stake > bankroll * config.max_exposure_league,
            ),
            (
                "bookmaker_exposure_limit",
                bookmaker_exposure.get(key_bookmaker, 0.0)
                + executed_stake
                > bankroll * config.max_exposure_bookmaker,
            ),
        ]
        for reason, breached in breaches:
            if breached:
                executed_stake = 0.0
                skip_reason = reason
                break

        if executed_stake > 0:
            pnl = _pnl_for_result(str(row["result"]), float(row["captured_odds"]), executed_stake)
            daily_realized_pnl[bet_date] = daily_realized_pnl.get(bet_date, 0.0) + pnl
            market_exposure[key_market] = market_exposure.get(key_market, 0.0) + executed_stake
            league_exposure[key_league] = league_exposure.get(key_league, 0.0) + executed_stake
            bookmaker_exposure[key_bookmaker] = bookmaker_exposure.get(key_bookmaker, 0.0) + executed_stake
            result = str(row["result"])
        else:
            pnl = 0.0
            result = "skipped"

        bankroll_after = bankroll + pnl
        rows.append(
            {
                "bet_id": row["bet_id"],
                "method": config.method,
                "placed_ts": row["placed_ts"],
                "bankroll_before": round(bankroll, 2),
                "planned_stake": round(planned_stake, 2),
                "executed_stake": round(executed_stake, 2),
                "pnl": round(pnl, 2),
                "result": result,
                "skip_reason": skip_reason,
                "bankroll_after": round(bankroll_after, 2),
                "league": row["league"],
                "market": row["market"],
                "strategy": row["strategy"],
            }
        )
        bankroll = bankroll_after

    simulation_df = pd.DataFrame(rows)
    if not simulation_df.empty:
        simulation_df["equity_peak"] = simulation_df["bankroll_after"].cummax()
        simulation_df["drawdown"] = (simulation_df["bankroll_after"] / simulation_df["equity_peak"]) - 1.0
    return simulation_df


def summarize_simulation(sim_df: pd.DataFrame, initial_bankroll: float = 10_000.0) -> dict:
    if sim_df.empty:
        return {
            "method": "unknown",
            "final_bankroll": initial_bankroll,
            "net_profit": 0.0,
            "roi": 0.0,
            "max_drawdown": 0.0,
            "executed_bets": 0,
            "skipped_bets": 0,
        }
    final_bankroll = float(sim_df["bankroll_after"].iloc[-1])
    net_profit = final_bankroll - initial_bankroll
    executed_mask = sim_df["executed_stake"] > 0
    max_drawdown = calculate_drawdown(sim_df.loc[executed_mask, "bankroll_after"]) if executed_mask.any() else 0.0

    return {
        "method": str(sim_df["method"].iloc[0]),
        "final_bankroll": round(final_bankroll, 2),
        "net_profit": round(net_profit, 2),
        "roi": round(net_profit / initial_bankroll, 4) if initial_bankroll else 0.0,
        "max_drawdown": round(max_drawdown, 4),
        "executed_bets": int(executed_mask.sum()),
        "skipped_bets": int((~executed_mask).sum()),
    }


def compare_default_scenarios(
    bets_df: pd.DataFrame, initial_bankroll: float = 10_000.0
) -> tuple[pd.DataFrame, pd.DataFrame]:
    configs = [
        SimulationConfig(method="fixed", initial_bankroll=initial_bankroll, fixed_stake=100.0),
        SimulationConfig(method="percentage", initial_bankroll=initial_bankroll, pct_stake=0.015),
        SimulationConfig(method="kelly", initial_bankroll=initial_bankroll, kelly_fraction=0.4),
    ]
    all_runs: list[pd.DataFrame] = []
    summaries: list[dict] = []
    for conf in configs:
        run_df = simulate_bankroll(bets_df, conf)
        all_runs.append(run_df)
        summaries.append(summarize_simulation(run_df, initial_bankroll=initial_bankroll))

    combined_runs = pd.concat(all_runs, ignore_index=True) if all_runs else pd.DataFrame()
    summary_df = pd.DataFrame(summaries)
    return combined_runs, summary_df
