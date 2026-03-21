from __future__ import annotations

import argparse
import shutil

from src.analytics.mart_builder import build_analytics_marts, materialize_to_duckdb
from src.cleaning.standardize import clean_bets, clean_matches, persist_staging
from src.config.settings import DEFAULT_INITIAL_BANKROLL, DEFAULT_SEED, PATHS, ensure_directories
from src.ingestion.ingest_pipeline import load_raw_data, seed_raw_data
from src.risk.risk_scoring import compute_risk_scores
from src.simulation.bankroll_simulator import compare_default_scenarios
from src.utils.io import write_tables_to_csv
from src.utils.logger import get_logger
from src.validation.data_quality import assert_critical_quality, run_data_quality_checks

logger = get_logger(__name__)


def run_seed(num_matches: int, seed: int) -> None:
    ensure_directories()
    seed_raw_data(num_matches=num_matches, seed=seed)


def run_pipeline(fail_on_dq_error: bool) -> None:
    ensure_directories()
    try:
        raw_matches, raw_bets = load_raw_data()
    except FileNotFoundError:
        logger.info("Raw data not found, generating synthetic input first.")
        raw_matches, raw_bets = seed_raw_data(num_matches=500, seed=DEFAULT_SEED)

    matches = clean_matches(raw_matches)
    bets = clean_bets(raw_bets, matches)
    persist_staging(matches, bets)

    dq_report = run_data_quality_checks(matches, bets)
    if fail_on_dq_error:
        assert_critical_quality(dq_report)

    marts = build_analytics_marts(matches, bets, initial_bankroll=DEFAULT_INITIAL_BANKROLL)
    risk_scores_df, risk_alerts_df = compute_risk_scores(
        bets_df=bets, initial_bankroll=DEFAULT_INITIAL_BANKROLL
    )
    sim_runs_df, sim_summary_df = compare_default_scenarios(
        bets_df=bets, initial_bankroll=DEFAULT_INITIAL_BANKROLL
    )

    marts.update(
        {
            "mart_risk_scores": risk_scores_df,
            "mart_risk_alerts": risk_alerts_df,
            "fact_bankroll_scenarios": sim_runs_df,
            "mart_bankroll_scenarios_summary": sim_summary_df,
            "data_quality_report": dq_report,
        }
    )

    write_tables_to_csv(marts, PATHS.marts_dir)
    materialize_to_duckdb(marts, PATHS.warehouse_path)

    logger.info("Pipeline finished.")
    logger.info("Marts generated: %s", ", ".join(sorted(marts.keys())))
    logger.info("Warehouse: %s", PATHS.warehouse_path)


def run_clean() -> None:
    for target in (PATHS.raw_dir, PATHS.staging_dir, PATHS.marts_dir):
        if target.exists():
            shutil.rmtree(target)
        target.mkdir(parents=True, exist_ok=True)
    if PATHS.warehouse_path.exists():
        PATHS.warehouse_path.unlink()
    logger.info("Cleaned raw, staging, marts and warehouse artifacts.")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Sports Betting Intelligence Engine CLI")
    subparsers = parser.add_subparsers(dest="command")

    seed_cmd = subparsers.add_parser("seed", help="Generate synthetic raw data")
    seed_cmd.add_argument("--matches", type=int, default=500, help="Number of matches to generate")
    seed_cmd.add_argument("--seed", type=int, default=DEFAULT_SEED, help="Random seed")

    pipeline_cmd = subparsers.add_parser("pipeline", help="Run full analytics pipeline")
    pipeline_cmd.add_argument(
        "--fail-on-dq-error",
        action="store_true",
        help="Fail pipeline when critical data quality checks fail",
    )

    subparsers.add_parser("clean", help="Clean generated data artifacts")
    return parser


def main() -> None:
    parser = build_parser()
    args = parser.parse_args()

    if args.command == "seed":
        run_seed(num_matches=args.matches, seed=args.seed)
        return
    if args.command == "pipeline":
        run_pipeline(fail_on_dq_error=args.fail_on_dq_error)
        return
    if args.command == "clean":
        run_clean()
        return

    parser.print_help()


if __name__ == "__main__":
    main()
