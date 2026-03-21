from __future__ import annotations

from src.ingestion.synthetic_data import (
    STRATEGIES,
    _decimal_odds,
    _resolve_market_result,
    _settle_bet,
    generate_synthetic_data,
)


def test_generate_synthetic_data_shape() -> None:
    matches, bets = generate_synthetic_data(num_matches=50, seed=7)
    assert len(matches) == 50
    assert len(bets) > 0
    assert {"match_id", "league", "kickoff_ts"}.issubset(set(matches.columns))
    assert {"bet_id", "captured_odds", "result", "stake"}.issubset(set(bets.columns))


def test_synthetic_odds_and_stake_constraints() -> None:
    _, bets = generate_synthetic_data(num_matches=80, seed=11)
    assert (bets["captured_odds"] > 1).all()
    assert (bets["closing_odds"] > 1).all()
    assert (bets["stake"] >= 0).all()


def test_all_strategies_present() -> None:
    _, bets = generate_synthetic_data(num_matches=200, seed=42)
    expected = {s.name for s in STRATEGIES}
    assert set(bets["strategy"].unique()) == expected


def test_reproducible_with_same_seed() -> None:
    m1, b1 = generate_synthetic_data(num_matches=30, seed=99)
    m2, b2 = generate_synthetic_data(num_matches=30, seed=99)
    assert m1.equals(m2)
    assert b1.equals(b2)


def test_resolve_market_moneyline() -> None:
    assert _resolve_market_result("MONEYLINE_HOME", 2, 1) == "win"
    assert _resolve_market_result("MONEYLINE_HOME", 1, 2) == "loss"
    assert _resolve_market_result("MONEYLINE_HOME", 1, 1) == "loss"


def test_resolve_market_over25() -> None:
    assert _resolve_market_result("OVER_2_5", 2, 1) == "win"
    assert _resolve_market_result("OVER_2_5", 1, 0) == "loss"


def test_resolve_market_btts() -> None:
    assert _resolve_market_result("BTTS_YES", 1, 1) == "win"
    assert _resolve_market_result("BTTS_YES", 2, 0) == "loss"


def test_resolve_market_dnb() -> None:
    assert _resolve_market_result("DNB_HOME", 2, 1) == "win"
    assert _resolve_market_result("DNB_HOME", 1, 1) == "push"
    assert _resolve_market_result("DNB_HOME", 0, 1) == "loss"


def test_settle_bet_outcomes() -> None:
    assert _settle_bet("win", 100.0, 2.5) == 150.0
    assert _settle_bet("push", 100.0, 2.5) == 0.0
    assert _settle_bet("loss", 100.0, 2.5) == -100.0


def test_decimal_odds_always_above_one() -> None:
    for prob in [0.1, 0.3, 0.5, 0.7, 0.9]:
        odds = _decimal_odds(prob, margin=0.05)
        assert odds >= 1.05
