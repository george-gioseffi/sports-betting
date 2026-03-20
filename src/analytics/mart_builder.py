from __future__ import annotations

import pandas as pd

from src.analytics.metrics_calculator import (
    calculate_core_metrics,
    compute_bankroll_curve,
    monthly_performance,
    performance_by_dimension,
)
from src.models.warehouse import write_tables_to_duckdb


def _build_dimension(df: pd.DataFrame, column: str, key_name: str) -> pd.DataFrame:
    dim = pd.DataFrame({column: sorted(df[column].dropna().astype(str).unique())})
    dim[key_name] = range(1, len(dim) + 1)
    return dim[[key_name, column]]


def build_dimensions(matches_df: pd.DataFrame, bets_df: pd.DataFrame) -> dict[str, pd.DataFrame]:
    dim_date = pd.DataFrame(
        {
            "date": sorted(
                pd.concat(
                    [
                        pd.to_datetime(matches_df["kickoff_ts"]).dt.date.astype(str),
                        pd.to_datetime(bets_df["placed_ts"]).dt.date.astype(str),
                        pd.to_datetime(bets_df["settled_ts"]).dt.date.astype(str),
                    ],
                    axis=0,
                ).unique()
            )
        }
    )
    dim_date["date_id"] = range(1, len(dim_date) + 1)
    dim_date["year"] = pd.to_datetime(dim_date["date"]).dt.year
    dim_date["month"] = pd.to_datetime(dim_date["date"]).dt.month
    dim_date["day"] = pd.to_datetime(dim_date["date"]).dt.day
    dim_date["week"] = pd.to_datetime(dim_date["date"]).dt.isocalendar().week.astype(int)

    dim_league = _build_dimension(matches_df, "league", "league_id")
    team_values = pd.concat([matches_df["home_team"], matches_df["away_team"]], axis=0)
    dim_team = pd.DataFrame({"team_name": sorted(team_values.dropna().astype(str).unique())})
    dim_team["team_id"] = range(1, len(dim_team) + 1)
    dim_team = dim_team[["team_id", "team_name"]]

    dim_market = _build_dimension(bets_df, "market", "market_id")
    dim_strategy = _build_dimension(bets_df, "strategy", "strategy_id")
    dim_bookmaker = _build_dimension(bets_df, "bookmaker", "bookmaker_id")

    return {
        "dim_date": dim_date[["date_id", "date", "year", "month", "day", "week"]],
        "dim_league": dim_league,
        "dim_team": dim_team,
        "dim_market": dim_market,
        "dim_strategy": dim_strategy,
        "dim_bookmaker": dim_bookmaker,
    }


def build_fact_matches(matches_df: pd.DataFrame, dims: dict[str, pd.DataFrame]) -> pd.DataFrame:
    fact = matches_df.copy()
    fact["kickoff_date"] = pd.to_datetime(fact["kickoff_ts"]).dt.date.astype(str)
    fact = fact.merge(dims["dim_league"], on="league", how="left")
    fact = fact.merge(
        dims["dim_team"].rename(columns={"team_id": "home_team_id", "team_name": "home_team"}),
        on="home_team",
        how="left",
    )
    fact = fact.merge(
        dims["dim_team"].rename(columns={"team_id": "away_team_id", "team_name": "away_team"}),
        on="away_team",
        how="left",
    )
    fact = fact.merge(
        dims["dim_date"].rename(columns={"date_id": "kickoff_date_id", "date": "kickoff_date"}),
        on="kickoff_date",
        how="left",
    )
    return fact[
        [
            "match_id",
            "season",
            "league_id",
            "home_team_id",
            "away_team_id",
            "kickoff_ts",
            "kickoff_date_id",
            "home_goals",
            "away_goals",
            "total_goals",
        ]
    ]


def build_fact_bets(bets_df: pd.DataFrame, dims: dict[str, pd.DataFrame]) -> pd.DataFrame:
    fact = bets_df.copy()
    fact["placed_date"] = pd.to_datetime(fact["placed_ts"]).dt.date.astype(str)
    fact["settled_date"] = pd.to_datetime(fact["settled_ts"]).dt.date.astype(str)

    fact = fact.merge(dims["dim_market"], on="market", how="left")
    fact = fact.merge(dims["dim_strategy"], on="strategy", how="left")
    fact = fact.merge(dims["dim_bookmaker"], on="bookmaker", how="left")
    fact = fact.merge(dims["dim_league"], on="league", how="left")
    fact = fact.merge(
        dims["dim_date"].rename(columns={"date_id": "placed_date_id", "date": "placed_date"}),
        on="placed_date",
        how="left",
    )
    fact = fact.merge(
        dims["dim_date"].rename(columns={"date_id": "settled_date_id", "date": "settled_date"}),
        on="settled_date",
        how="left",
    )

    return fact[
        [
            "bet_id",
            "match_id",
            "strategy_id",
            "bookmaker_id",
            "market_id",
            "league_id",
            "placed_date_id",
            "settled_date_id",
            "captured_odds",
            "closing_odds",
            "stake",
            "result",
            "payout",
            "pnl",
            "clv",
            "odds_band",
        ]
    ]


def build_analytics_marts(
    matches_df: pd.DataFrame, bets_df: pd.DataFrame, initial_bankroll: float = 10_000.0
) -> dict[str, pd.DataFrame]:
    dims = build_dimensions(matches_df, bets_df)
    fact_matches = build_fact_matches(matches_df, dims)
    fact_bets = build_fact_bets(bets_df, dims)

    fact_odds_snapshots = bets_df[
        [
            "bet_id",
            "match_id",
            "bookmaker",
            "market",
            "placed_ts",
            "captured_odds",
            "closing_odds",
            "clv",
        ]
    ].copy()
    fact_odds_snapshots = fact_odds_snapshots.rename(columns={"placed_ts": "snapshot_ts"})

    fact_results = bets_df[["bet_id", "match_id", "result", "stake", "pnl"]].copy()

    overall_metrics = pd.DataFrame([calculate_core_metrics(bets_df, initial_bankroll=initial_bankroll)])
    segment_cols = {
        "mart_strategy_performance": "strategy",
        "mart_market_performance": "market",
        "mart_league_performance": "league",
        "mart_bookmaker_performance": "bookmaker",
        "mart_odds_band_performance": "odds_band",
    }
    segment_marts = {
        table_name: performance_by_dimension(
            bets_df,
            group_col=group_col,
            initial_bankroll=initial_bankroll,
        )
        for table_name, group_col in segment_cols.items()
    }

    strategy_performance = segment_marts["mart_strategy_performance"]
    monthly_perf = monthly_performance(bets_df)
    bankroll_evolution = compute_bankroll_curve(bets_df, initial_bankroll=initial_bankroll)

    tables: dict[str, pd.DataFrame] = {
        **dims,
        "fact_matches": fact_matches,
        "fact_bets": fact_bets,
        "fact_odds_snapshots": fact_odds_snapshots,
        "fact_results": fact_results,
        "fact_strategy_performance": strategy_performance,
        "fact_bankroll_evolution": bankroll_evolution,
        "kpi_overall": overall_metrics,
        "mart_strategy_performance": strategy_performance,
        "mart_monthly_performance": monthly_perf,
    }
    tables.update(segment_marts)
    return tables


def materialize_to_duckdb(tables: dict[str, pd.DataFrame], warehouse_path) -> None:
    write_tables_to_duckdb(tables=tables, warehouse_path=warehouse_path)
