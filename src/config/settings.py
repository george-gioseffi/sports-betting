from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path

from dotenv import load_dotenv

load_dotenv()


@dataclass(frozen=True)
class Paths:
    base_dir: Path
    data_dir: Path
    raw_dir: Path
    staging_dir: Path
    marts_dir: Path
    samples_dir: Path
    warehouse_path: Path
    docs_dir: Path
    sql_dir: Path


BASE_DIR = Path(__file__).resolve().parents[2]
DATA_DIR = Path(os.getenv("DATA_DIR", BASE_DIR / "data"))
RAW_DIR = DATA_DIR / "raw"
STAGING_DIR = DATA_DIR / "staging"
MARTS_DIR = DATA_DIR / "marts"
SAMPLES_DIR = DATA_DIR / "samples"
WAREHOUSE_PATH = Path(os.getenv("WAREHOUSE_PATH", DATA_DIR / "warehouse.duckdb"))
DOCS_DIR = BASE_DIR / "docs"
SQL_DIR = BASE_DIR / "sql"

PATHS = Paths(
    base_dir=BASE_DIR,
    data_dir=DATA_DIR,
    raw_dir=RAW_DIR,
    staging_dir=STAGING_DIR,
    marts_dir=MARTS_DIR,
    samples_dir=SAMPLES_DIR,
    warehouse_path=WAREHOUSE_PATH,
    docs_dir=DOCS_DIR,
    sql_dir=SQL_DIR,
)

DEFAULT_INITIAL_BANKROLL = float(os.getenv("INITIAL_BANKROLL", "10000"))
DEFAULT_SEED = int(os.getenv("DEFAULT_SEED", "42"))

ALLOWED_RESULTS = {"win", "loss", "push"}
ALLOWED_MARKETS = {"MONEYLINE_HOME", "OVER_2_5", "BTTS_YES", "DNB_HOME"}
ALLOWED_STRATEGY_PROFILES = {"Conservative", "Moderate", "Aggressive"}

MARKET_NORMALIZATION = {
    "1x2_home": "MONEYLINE_HOME",
    "home_win": "MONEYLINE_HOME",
    "moneyline_home": "MONEYLINE_HOME",
    "over2.5": "OVER_2_5",
    "over_2_5": "OVER_2_5",
    "btts_yes": "BTTS_YES",
    "both_teams_score_yes": "BTTS_YES",
    "dnb_home": "DNB_HOME",
    "draw_no_bet_home": "DNB_HOME",
}

MARKET_LABELS = {
    "MONEYLINE_HOME": "Moneyline Home",
    "OVER_2_5": "Over 2.5 Goals",
    "BTTS_YES": "Both Teams To Score (Yes)",
    "DNB_HOME": "Draw No Bet Home",
}

RISK_LIMITS = {
    "daily_loss_limit": 0.08,
    "max_exposure_market": 0.12,
    "max_exposure_league": 0.25,
    "max_exposure_bookmaker": 0.18,
    "max_drawdown_threshold": 0.2,
}


def ensure_directories() -> None:
    for directory in [
        PATHS.data_dir,
        PATHS.raw_dir,
        PATHS.staging_dir,
        PATHS.marts_dir,
        PATHS.samples_dir,
        PATHS.docs_dir,
        PATHS.sql_dir,
    ]:
        directory.mkdir(parents=True, exist_ok=True)
