from __future__ import annotations

import pandas as pd

from src.config.settings import MARKET_NORMALIZATION, PATHS
from src.utils.io import write_csv


def normalize_team_name(name: str) -> str:
    return " ".join(str(name).strip().split()).title()


def normalize_market_name(market: str) -> str:
    market_key = str(market).strip().lower()
    return MARKET_NORMALIZATION.get(market_key, str(market).strip().upper())


def _to_datetime(df: pd.DataFrame, columns: list[str]) -> pd.DataFrame:
    out = df.copy()
    for col in columns:
        out[col] = pd.to_datetime(out[col], errors="coerce")
    return out


def clean_matches(matches_df: pd.DataFrame) -> pd.DataFrame:
    cleaned = matches_df.copy()
    cleaned["home_team"] = cleaned["home_team"].map(normalize_team_name)
    cleaned["away_team"] = cleaned["away_team"].map(normalize_team_name)
    cleaned = _to_datetime(cleaned, ["kickoff_ts"])
    cleaned = cleaned.drop_duplicates(subset=["match_id"]).sort_values("kickoff_ts")
    cleaned["total_goals"] = cleaned["home_goals"] + cleaned["away_goals"]
    return cleaned.reset_index(drop=True)


def clean_bets(bets_df: pd.DataFrame, matches_df: pd.DataFrame) -> pd.DataFrame:
    cleaned = bets_df.copy()
    cleaned["market"] = cleaned["market"].map(normalize_market_name)
    cleaned = _to_datetime(cleaned, ["placed_ts", "settled_ts"])
    cleaned["result"] = cleaned["result"].astype(str).str.lower().str.strip()
    cleaned["strategy"] = cleaned["strategy"].astype(str).str.strip()
    cleaned["bookmaker"] = cleaned["bookmaker"].astype(str).str.strip()
    cleaned["captured_odds"] = pd.to_numeric(cleaned["captured_odds"], errors="coerce")
    cleaned["closing_odds"] = pd.to_numeric(cleaned["closing_odds"], errors="coerce")
    cleaned["stake"] = pd.to_numeric(cleaned["stake"], errors="coerce")
    cleaned["pnl"] = pd.to_numeric(cleaned["pnl"], errors="coerce")
    cleaned["clv"] = pd.to_numeric(cleaned["clv"], errors="coerce")

    cleaned = cleaned.drop_duplicates(subset=["bet_id"])

    league_map = matches_df[["match_id", "league"]].drop_duplicates()
    cleaned = cleaned.drop(columns=["league"], errors="ignore").merge(
        league_map, on="match_id", how="left"
    )

    cleaned["odds_band"] = pd.cut(
        cleaned["captured_odds"],
        bins=[1.0, 1.5, 2.0, 2.5, 3.0, 10.0],
        labels=["1.01-1.50", "1.51-2.00", "2.01-2.50", "2.51-3.00", "3.01+"],
        include_lowest=True,
    ).astype(str)

    cleaned = cleaned.sort_values(["placed_ts", "bet_id"]).reset_index(drop=True)
    return cleaned


def persist_staging(matches_df: pd.DataFrame, bets_df: pd.DataFrame) -> None:
    write_csv(matches_df, PATHS.staging_dir / "matches_staging.csv")
    write_csv(bets_df, PATHS.staging_dir / "bets_staging.csv")
