from __future__ import annotations

import pandas as pd

from src.risk.risk_scoring import _classify_profile, _clip01, compute_risk_scores


def test_risk_scores_output(sample_bets) -> None:
    risk_scores, alerts = compute_risk_scores(sample_bets, initial_bankroll=1_000.0)
    assert not risk_scores.empty
    assert {"strategy", "risk_score", "risk_profile"}.issubset(set(risk_scores.columns))
    assert risk_scores["risk_profile"].isin(["Conservative", "Moderate", "Aggressive"]).all()
    assert not alerts.empty


def test_risk_scores_empty_input() -> None:
    empty = pd.DataFrame(
        columns=[
            "strategy",
            "stake",
            "pnl",
            "settled_ts",
            "result",
            "league",
            "captured_odds",
            "closing_odds",
            "clv",
        ]
    )
    scores, alerts = compute_risk_scores(empty)
    assert scores.empty
    assert alerts.empty


def test_classify_profile_boundaries() -> None:
    assert _classify_profile(0) == "Conservative"
    assert _classify_profile(33) == "Conservative"
    assert _classify_profile(34) == "Moderate"
    assert _classify_profile(66) == "Moderate"
    assert _classify_profile(67) == "Aggressive"
    assert _classify_profile(100) == "Aggressive"


def test_clip01_boundaries() -> None:
    assert _clip01(-0.5) == 0.0
    assert _clip01(0.5) == 0.5
    assert _clip01(1.5) == 1.0


def test_risk_score_range(sample_bets) -> None:
    scores, _ = compute_risk_scores(sample_bets, initial_bankroll=1_000.0)
    assert (scores["risk_score"] >= 0).all()
    assert (scores["risk_score"] <= 100).all()


def test_component_scores_present(sample_bets) -> None:
    scores, _ = compute_risk_scores(sample_bets, initial_bankroll=1_000.0)
    expected = {
        "volatility_score",
        "drawdown_score",
        "stake_score",
        "concentration_score",
        "clv_score",
        "streak_score",
    }
    assert expected.issubset(set(scores.columns))
