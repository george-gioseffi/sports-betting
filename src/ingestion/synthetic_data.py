from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta

import numpy as np
import pandas as pd


LEAGUE_TEAMS: dict[str, list[str]] = {
    "Premier League": ["Arsenal", "Liverpool", "Chelsea", "Tottenham", "Newcastle", "Aston Villa"],
    "La Liga": ["Real Madrid", "Barcelona", "Atletico Madrid", "Real Sociedad", "Sevilla", "Valencia"],
    "Serie A": ["Inter", "Juventus", "Milan", "Napoli", "Roma", "Atalanta"],
    "Brasileirao": ["Flamengo", "Palmeiras", "Sao Paulo", "Atletico MG", "Fluminense", "Internacional"],
}

BOOKMAKERS = ["Pinnacle", "Bet365", "Betano", "1xBet", "Stake"]
MARKETS = ["MONEYLINE_HOME", "OVER_2_5", "BTTS_YES", "DNB_HOME"]


@dataclass(frozen=True)
class StrategyConfig:
    name: str
    bet_probability: float
    clv_bias: float
    stake_mean: float
    stake_std: float
    market_weights: tuple[float, float, float, float]


STRATEGIES = [
    StrategyConfig(
        name="Quant_Value",
        bet_probability=0.44,
        clv_bias=0.018,
        stake_mean=75.0,
        stake_std=18.0,
        market_weights=(0.35, 0.30, 0.20, 0.15),
    ),
    StrategyConfig(
        name="League_Specialist",
        bet_probability=0.38,
        clv_bias=0.010,
        stake_mean=90.0,
        stake_std=25.0,
        market_weights=(0.40, 0.20, 0.18, 0.22),
    ),
    StrategyConfig(
        name="Aggressive_Momentum",
        bet_probability=0.52,
        clv_bias=-0.009,
        stake_mean=130.0,
        stake_std=35.0,
        market_weights=(0.28, 0.34, 0.26, 0.12),
    ),
]


def _sigmoid(x: float) -> float:
    return 1.0 / (1.0 + np.exp(-x))


def _decimal_odds(probability: float, margin: float) -> float:
    probability = float(np.clip(probability, 0.02, 0.96))
    return round(max(1.05, 1.0 / (probability * (1 + margin))), 2)


def _resolve_market_result(market: str, home_goals: int, away_goals: int) -> str:
    total_goals = home_goals + away_goals
    if market == "MONEYLINE_HOME":
        return "win" if home_goals > away_goals else "loss"
    if market == "OVER_2_5":
        return "win" if total_goals >= 3 else "loss"
    if market == "BTTS_YES":
        return "win" if home_goals > 0 and away_goals > 0 else "loss"
    if market == "DNB_HOME":
        if home_goals > away_goals:
            return "win"
        if home_goals == away_goals:
            return "push"
        return "loss"
    raise ValueError(f"Unsupported market: {market}")


def _settle_bet(result: str, stake: float, odds: float) -> float:
    if result == "win":
        return round(stake * (odds - 1.0), 2)
    if result == "push":
        return 0.0
    return round(-stake, 2)


def _probabilities(diff: float, lambda_home: float, lambda_away: float) -> dict[str, float]:
    base_home = _sigmoid((diff + 0.18) / 0.45)
    draw_prob = float(np.clip(0.25 - abs(diff) * 0.08, 0.12, 0.29))
    home_prob = (1 - draw_prob) * base_home
    away_prob = max(0.02, 1.0 - draw_prob - home_prob)
    dnb_home_prob = float(np.clip(home_prob / (home_prob + away_prob), 0.05, 0.95))
    over_prob = float(np.clip(_sigmoid((lambda_home + lambda_away - 2.45) / 0.45), 0.08, 0.92))
    btts_prob = float(np.clip(_sigmoid((min(lambda_home, lambda_away) - 0.55) / 0.35), 0.08, 0.92))
    return {
        "MONEYLINE_HOME": float(np.clip(home_prob, 0.05, 0.90)),
        "OVER_2_5": over_prob,
        "BTTS_YES": btts_prob,
        "DNB_HOME": dnb_home_prob,
    }


def generate_synthetic_data(num_matches: int = 280, seed: int = 42) -> tuple[pd.DataFrame, pd.DataFrame]:
    rng = np.random.default_rng(seed)
    start_date = datetime(2025, 1, 1, 15, 0, 0)

    all_teams = [team for teams in LEAGUE_TEAMS.values() for team in teams]
    team_strength = {team: rng.normal(0, 0.55) for team in all_teams}

    match_rows = []
    bet_rows = []
    bet_id = 1

    for idx in range(1, num_matches + 1):
        league = rng.choice(list(LEAGUE_TEAMS.keys()), p=[0.30, 0.26, 0.22, 0.22])
        home_team, away_team = rng.choice(LEAGUE_TEAMS[league], size=2, replace=False)
        kickoff_ts = start_date + timedelta(days=idx // 4, hours=int(rng.integers(0, 9)))

        home_rating = team_strength[home_team] + 0.18
        away_rating = team_strength[away_team]
        diff = home_rating - away_rating
        lambda_home = float(np.clip(1.35 + diff * 0.55, 0.35, 3.2))
        lambda_away = float(np.clip(1.10 - diff * 0.45, 0.30, 3.0))
        home_goals = int(rng.poisson(lambda_home))
        away_goals = int(rng.poisson(lambda_away))

        probs = _probabilities(diff, lambda_home, lambda_away)
        match_id = f"M{idx:05d}"

        match_rows.append(
            {
                "match_id": match_id,
                "season": "2025/2026",
                "league": league,
                "home_team": home_team,
                "away_team": away_team,
                "kickoff_ts": kickoff_ts,
                "home_goals": home_goals,
                "away_goals": away_goals,
            }
        )

        for strategy in STRATEGIES:
            if rng.random() > strategy.bet_probability:
                continue
            market = str(rng.choice(MARKETS, p=strategy.market_weights))
            bookmaker = str(rng.choice(BOOKMAKERS))
            p_true = probs[market]
            closing_odds = _decimal_odds(p_true, margin=float(rng.uniform(0.03, 0.08)))
            captured_odds = round(max(1.05, closing_odds * (1 + rng.normal(strategy.clv_bias, 0.03))), 2)
            stake = round(max(10.0, rng.normal(strategy.stake_mean, strategy.stake_std)), 2)
            placed_ts = kickoff_ts - timedelta(hours=int(rng.integers(6, 96)))
            settled_ts = kickoff_ts + timedelta(hours=2)

            result = _resolve_market_result(market, home_goals, away_goals)
            pnl = _settle_bet(result=result, stake=stake, odds=captured_odds)
            payout = round(stake + pnl, 2) if result in {"win", "push"} else 0.0
            clv = round((captured_odds / closing_odds) - 1, 4)

            bet_rows.append(
                {
                    "bet_id": f"B{bet_id:06d}",
                    "match_id": match_id,
                    "strategy": strategy.name,
                    "bookmaker": bookmaker,
                    "market": market,
                    "selection": "HOME" if market in {"MONEYLINE_HOME", "DNB_HOME"} else "YES",
                    "captured_odds": captured_odds,
                    "closing_odds": closing_odds,
                    "stake": stake,
                    "placed_ts": placed_ts,
                    "settled_ts": settled_ts,
                    "result": result,
                    "payout": payout,
                    "pnl": pnl,
                    "clv": clv,
                    "league": league,
                }
            )
            bet_id += 1

    matches = pd.DataFrame(match_rows).sort_values("kickoff_ts").reset_index(drop=True)
    bets = pd.DataFrame(bet_rows).sort_values("placed_ts").reset_index(drop=True)
    return matches, bets
