from __future__ import annotations

import pandas as pd
import pytest

from src.analytics.metrics_calculator import (
    calculate_core_metrics,
    calculate_drawdown,
    calculate_sharpe_like,
    calculate_streaks,
    compute_bankroll_curve,
    monthly_performance,
    performance_by_dimension,
)


def test_core_metrics_basic(sample_bets) -> None:
    metrics = calculate_core_metrics(sample_bets, initial_bankroll=1_000.0)
    assert metrics["total_bets"] == 3
    assert metrics["settled_bets"] == 3
    assert metrics["net_profit"] == pytest.approx(50.0)
    assert metrics["total_stake"] == pytest.approx(240.0)
    assert metrics["win_rate"] == pytest.approx(1 / 3, rel=1e-2)
    assert metrics["loss_rate"] == pytest.approx(1 / 3, rel=1e-2)
    assert metrics["push_rate"] == pytest.approx(1 / 3, rel=1e-2)
    assert metrics["roi"] == pytest.approx(0.05, rel=1e-2)
    assert metrics["yield_pct"] == pytest.approx(50.0 / 240.0, rel=1e-2)


def test_core_metrics_empty_dataframe() -> None:
    empty = pd.DataFrame(columns=["result", "stake", "pnl", "captured_odds", "clv", "settled_ts"])
    metrics = calculate_core_metrics(empty)
    assert metrics["total_bets"] == 0
    assert metrics["net_profit"] == 0.0
    assert metrics["yield_pct"] == 0.0


def test_drawdown_known_curve() -> None:
    curve = pd.Series([100, 110, 105, 115, 90, 95])
    dd = calculate_drawdown(curve)
    # peak at 115, trough at 90 -> drawdown = 1 - 90/115 = 0.2174
    assert dd == pytest.approx(1 - 90 / 115, abs=1e-4)


def test_drawdown_monotonically_increasing() -> None:
    curve = pd.Series([100, 110, 120, 130])
    dd = calculate_drawdown(curve)
    assert dd == pytest.approx(0.0)


def test_drawdown_empty() -> None:
    assert calculate_drawdown(pd.Series(dtype=float)) == 0.0


def test_streaks_known_sequence() -> None:
    results = pd.Series(["win", "win", "win", "loss", "loss", "win"])
    green, red = calculate_streaks(results)
    assert green == 3
    assert red == 2


def test_streaks_with_pushes() -> None:
    results = pd.Series(["win", "win", "push", "win", "win", "win"])
    green, red = calculate_streaks(results)
    assert green == 3  # push resets the streak
    assert red == 0


def test_sharpe_like_positive_returns() -> None:
    returns = pd.Series([0.01, 0.02, 0.01, 0.015, 0.005])
    sharpe = calculate_sharpe_like(returns)
    assert sharpe > 0


def test_sharpe_like_zero_std() -> None:
    returns = pd.Series([0.01, 0.01, 0.01])
    assert calculate_sharpe_like(returns) == 0.0


def test_sharpe_like_empty() -> None:
    assert calculate_sharpe_like(pd.Series(dtype=float)) == 0.0


def test_bankroll_curve_cumulates_daily_pnl(sample_bets) -> None:
    curve = compute_bankroll_curve(sample_bets, initial_bankroll=1000.0)
    assert not curve.empty
    assert "bankroll" in curve.columns
    assert "drawdown" in curve.columns


def test_performance_by_dimension(sample_bets) -> None:
    result = performance_by_dimension(sample_bets, "strategy")
    assert not result.empty
    assert "strategy" in result.columns
    assert len(result) == result["strategy"].nunique()


def test_monthly_performance_groups_by_month(sample_bets) -> None:
    result = monthly_performance(sample_bets)
    assert not result.empty
    assert "month" in result.columns
    assert "yield_pct" in result.columns


def test_profit_factor_all_wins() -> None:
    bets = pd.DataFrame(
        {
            "result": ["win", "win"],
            "stake": [100.0, 100.0],
            "pnl": [100.0, 50.0],
            "captured_odds": [2.0, 1.5],
            "clv": [0.05, 0.03],
            "settled_ts": ["2025-01-10 20:00", "2025-01-11 20:00"],
        }
    )
    metrics = calculate_core_metrics(bets, initial_bankroll=1000.0)
    assert metrics["profit_factor"] == float("inf")
    assert metrics["win_rate"] == pytest.approx(1.0)
