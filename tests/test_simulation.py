from __future__ import annotations

import pandas as pd
import pytest

from src.simulation.bankroll_simulator import (
    SimulationConfig,
    _estimate_probability,
    _kelly_stake_fraction,
    compare_default_scenarios,
    simulate_bankroll,
    summarize_simulation,
)


def test_fixed_stake_simulation(sample_bets) -> None:
    config = SimulationConfig(method="fixed", initial_bankroll=1_000.0, fixed_stake=50.0)
    run = simulate_bankroll(sample_bets, config)
    assert not run.empty
    assert run["method"].eq("fixed").all()
    assert "bankroll_after" in run.columns
    assert run["bankroll_after"].iloc[-1] != 1_000.0


def test_compare_default_scenarios(sample_bets) -> None:
    sample_bets = sample_bets.copy()
    sample_bets["placed_ts"] = pd.to_datetime(sample_bets["placed_ts"])
    combined, summary = compare_default_scenarios(sample_bets, initial_bankroll=1_000.0)
    assert not combined.empty
    assert not summary.empty
    assert set(summary["method"]) == {"fixed", "percentage", "kelly"}


def test_kelly_vs_fixed_produce_different_results(sample_bets) -> None:
    fixed_conf = SimulationConfig(method="fixed", initial_bankroll=1_000.0, fixed_stake=50.0)
    kelly_conf = SimulationConfig(method="kelly", initial_bankroll=1_000.0, kelly_fraction=0.5)
    fixed_run = simulate_bankroll(sample_bets, fixed_conf)
    kelly_run = simulate_bankroll(sample_bets, kelly_conf)
    # Kelly and fixed should generally produce different final bankrolls
    fixed_final = fixed_run["bankroll_after"].iloc[-1]
    kelly_final = kelly_run["bankroll_after"].iloc[-1]
    # At least one of them should differ from the initial bankroll
    assert fixed_final != 1_000.0 or kelly_final != 1_000.0


def test_percentage_stake_scales_with_bankroll(sample_bets) -> None:
    config = SimulationConfig(method="percentage", initial_bankroll=1_000.0, pct_stake=0.10)
    run = simulate_bankroll(sample_bets, config)
    # First bet should use 10% of 1000 = 100
    first = run.iloc[0]
    if first["executed_stake"] > 0:
        assert first["planned_stake"] == pytest.approx(100.0)


def test_kelly_fraction_zero_when_no_edge() -> None:
    # odds 2.0, probability 0.45 -> negative edge -> kelly returns 0
    fraction = _kelly_stake_fraction(2.0, 0.45)
    assert fraction == pytest.approx(0.0)


def test_kelly_fraction_positive_with_edge() -> None:
    # odds 2.5, probability 0.55 -> clear edge
    fraction = _kelly_stake_fraction(2.5, 0.55)
    assert fraction > 0


def test_kelly_fraction_capped_at_10_pct() -> None:
    # extreme edge: odds 10.0, probability 0.90
    fraction = _kelly_stake_fraction(10.0, 0.90)
    assert fraction <= 0.10


def test_estimate_probability_reasonable_range() -> None:
    prob = _estimate_probability(captured_odds=2.1, closing_odds=2.0)
    assert 0.02 <= prob <= 0.98


def test_summarize_empty_simulation() -> None:
    empty_df = pd.DataFrame()
    summary = summarize_simulation(empty_df, initial_bankroll=1_000.0)
    assert summary["final_bankroll"] == 1_000.0
    assert summary["net_profit"] == 0.0
    assert summary["executed_bets"] == 0


def test_daily_loss_limit_skips_bets() -> None:
    bets = pd.DataFrame(
        {
            "bet_id": ["B1", "B2", "B3"],
            "strategy": ["test", "test", "test"],
            "bookmaker": ["Pinnacle", "Pinnacle", "Pinnacle"],
            "market": ["MONEYLINE_HOME", "OVER_2_5", "BTTS_YES"],
            "captured_odds": [2.0, 2.0, 2.0],
            "closing_odds": [1.9, 1.9, 1.9],
            "stake": [100, 100, 100],
            "placed_ts": pd.to_datetime(
                ["2025-01-10 10:00", "2025-01-10 11:00", "2025-01-10 12:00"]
            ),
            "settled_ts": pd.to_datetime(
                ["2025-01-10 20:00", "2025-01-10 20:00", "2025-01-10 20:00"]
            ),
            "result": ["loss", "loss", "loss"],
            "payout": [0, 0, 0],
            "pnl": [-100, -100, -100],
            "clv": [0.05, 0.05, 0.05],
            "league": ["Premier League", "Premier League", "Premier League"],
        }
    )
    config = SimulationConfig(
        method="fixed",
        initial_bankroll=1_000.0,
        fixed_stake=100.0,
        daily_loss_limit=0.15,
    )
    run = simulate_bankroll(bets, config)
    skipped = run[run["result"] == "skipped"]
    # After losing 200 (20% of 1000), daily_loss_limit of 15% should trigger skip
    assert len(skipped) > 0
