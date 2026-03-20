from src.risk.risk_scoring import compute_risk_scores


def test_risk_scores_output(sample_bets) -> None:
    risk_scores, alerts = compute_risk_scores(sample_bets, initial_bankroll=1_000.0)
    assert not risk_scores.empty
    assert {"strategy", "risk_score", "risk_profile"}.issubset(set(risk_scores.columns))
    assert risk_scores["risk_profile"].isin(["Conservative", "Moderate", "Aggressive"]).all()
    assert not alerts.empty
