from __future__ import annotations

import pandas as pd

from src.config.settings import ALLOWED_MARKETS, ALLOWED_RESULTS, PATHS
from src.utils.io import write_csv


def run_data_quality_checks(matches_df: pd.DataFrame, bets_df: pd.DataFrame) -> pd.DataFrame:
    checks: list[dict[str, object]] = []

    def add_check(name: str, failed_rows: int, details: str, severity: str = "error") -> None:
        checks.append(
            {
                "check_name": name,
                "status": "passed" if failed_rows == 0 else "failed",
                "severity": severity,
                "failed_rows": int(failed_rows),
                "details": details,
            }
        )

    add_check(
        "match_id_not_null",
        int(matches_df["match_id"].isna().sum()),
        "match_id must be present in all match records",
    )
    add_check(
        "bet_id_not_null",
        int(bets_df["bet_id"].isna().sum()),
        "bet_id must be present in all betting records",
    )
    add_check(
        "match_id_unique",
        int(matches_df["match_id"].duplicated().sum()),
        "match_id must be unique in matches layer",
    )
    add_check(
        "bet_id_unique",
        int(bets_df["bet_id"].duplicated().sum()),
        "bet_id must be unique in bets layer",
    )
    add_check(
        "captured_odds_gt_1",
        int((bets_df["captured_odds"] <= 1).sum()),
        "captured_odds must be strictly greater than 1",
    )
    add_check(
        "closing_odds_gt_1",
        int((bets_df["closing_odds"] <= 1).sum()),
        "closing_odds must be strictly greater than 1",
    )
    add_check(
        "stake_non_negative",
        int((bets_df["stake"] < 0).sum()),
        "stake must be non-negative",
    )
    add_check(
        "result_domain_valid",
        int((~bets_df["result"].isin(ALLOWED_RESULTS)).sum()),
        "result must be one of: win/loss/push",
    )
    add_check(
        "market_domain_valid",
        int((~bets_df["market"].isin(ALLOWED_MARKETS)).sum()),
        "market must be standardized to the allowed domain",
    )
    add_check(
        "placed_before_settled",
        int((bets_df["placed_ts"] > bets_df["settled_ts"]).sum()),
        "bet placed timestamp cannot be later than settled timestamp",
    )

    kickoff_map = matches_df[["match_id", "kickoff_ts"]].drop_duplicates()
    tmp = bets_df.merge(kickoff_map, on="match_id", how="left")
    add_check(
        "placed_before_kickoff",
        int((tmp["placed_ts"] > tmp["kickoff_ts"]).sum()),
        "bets should be pre-match in this MVP dataset",
    )
    add_check(
        "settled_after_kickoff",
        int((tmp["settled_ts"] < tmp["kickoff_ts"]).sum()),
        "settlement timestamp must occur after kickoff",
    )
    add_check(
        "team_name_normalized",
        int(
            (
                matches_df["home_team"].str.contains(r"\s{2,}", regex=True).fillna(False)
                | matches_df["away_team"].str.contains(r"\s{2,}", regex=True).fillna(False)
            ).sum()
        ),
        "team names should be normalized and free of repeated spaces",
        severity="warning",
    )
    add_check(
        "stake_reasonable_upper_bound",
        int((bets_df["stake"] > 500).sum()),
        "stakes above 500 units are flagged as unusual",
        severity="warning",
    )

    report = pd.DataFrame(checks)
    write_csv(report, PATHS.marts_dir / "data_quality_report.csv")
    return report


def assert_critical_quality(report_df: pd.DataFrame) -> None:
    failed_critical = report_df[(report_df["status"] == "failed") & (report_df["severity"] == "error")]
    if not failed_critical.empty:
        formatted = failed_critical[["check_name", "failed_rows"]].to_dict("records")
        raise ValueError(f"Critical data quality checks failed: {formatted}")
