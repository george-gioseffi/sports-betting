import pandas as pd

from src.simulation.bankroll_simulator import (
    SimulationConfig,
    compare_default_scenarios,
    simulate_bankroll,
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
