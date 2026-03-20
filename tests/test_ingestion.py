from src.ingestion.synthetic_data import generate_synthetic_data


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
