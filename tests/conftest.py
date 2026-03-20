from __future__ import annotations

import pandas as pd
import pytest


@pytest.fixture
def sample_matches() -> pd.DataFrame:
    return pd.DataFrame(
        [
            {
                "match_id": "M00001",
                "season": "2025/2026",
                "league": "Premier League",
                "home_team": "Arsenal",
                "away_team": "Chelsea",
                "kickoff_ts": "2025-01-10 18:00:00",
                "home_goals": 2,
                "away_goals": 1,
                "total_goals": 3,
            },
            {
                "match_id": "M00002",
                "season": "2025/2026",
                "league": "La Liga",
                "home_team": "Barcelona",
                "away_team": "Sevilla",
                "kickoff_ts": "2025-01-11 18:00:00",
                "home_goals": 1,
                "away_goals": 1,
                "total_goals": 2,
            },
        ]
    )


@pytest.fixture
def sample_bets() -> pd.DataFrame:
    return pd.DataFrame(
        [
            {
                "bet_id": "B000001",
                "match_id": "M00001",
                "strategy": "Quant_Value",
                "bookmaker": "Pinnacle",
                "market": "MONEYLINE_HOME",
                "selection": "HOME",
                "captured_odds": 2.1,
                "closing_odds": 2.0,
                "stake": 100.0,
                "placed_ts": "2025-01-09 18:00:00",
                "settled_ts": "2025-01-10 20:00:00",
                "result": "win",
                "payout": 210.0,
                "pnl": 110.0,
                "clv": 0.05,
                "league": "Premier League",
                "odds_band": "2.01-2.50",
            },
            {
                "bet_id": "B000002",
                "match_id": "M00002",
                "strategy": "Aggressive_Momentum",
                "bookmaker": "Bet365",
                "market": "DNB_HOME",
                "selection": "HOME",
                "captured_odds": 1.8,
                "closing_odds": 1.75,
                "stake": 80.0,
                "placed_ts": "2025-01-10 12:00:00",
                "settled_ts": "2025-01-11 20:00:00",
                "result": "push",
                "payout": 80.0,
                "pnl": 0.0,
                "clv": 0.0286,
                "league": "La Liga",
                "odds_band": "1.51-2.00",
            },
            {
                "bet_id": "B000003",
                "match_id": "M00002",
                "strategy": "Aggressive_Momentum",
                "bookmaker": "Betano",
                "market": "OVER_2_5",
                "selection": "YES",
                "captured_odds": 2.2,
                "closing_odds": 2.15,
                "stake": 60.0,
                "placed_ts": "2025-01-10 10:00:00",
                "settled_ts": "2025-01-11 20:00:00",
                "result": "loss",
                "payout": 0.0,
                "pnl": -60.0,
                "clv": 0.0233,
                "league": "La Liga",
                "odds_band": "2.01-2.50",
            },
        ]
    )
