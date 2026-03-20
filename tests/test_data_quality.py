from src.validation.data_quality import run_data_quality_checks


def test_data_quality_passes_for_valid_data(sample_matches, sample_bets) -> None:
    report = run_data_quality_checks(sample_matches, sample_bets)
    critical_failed = report[(report["severity"] == "error") & (report["status"] == "failed")]
    assert critical_failed.empty


def test_data_quality_detects_invalid_odds(sample_matches, sample_bets) -> None:
    broken = sample_bets.copy()
    broken.loc[0, "captured_odds"] = 1.0
    report = run_data_quality_checks(sample_matches, broken)
    invalid_odds = report[report["check_name"] == "captured_odds_gt_1"]["status"].iloc[0]
    assert invalid_odds == "failed"
