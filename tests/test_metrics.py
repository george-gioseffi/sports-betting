import pytest

from src.analytics.metrics_calculator import calculate_core_metrics


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
