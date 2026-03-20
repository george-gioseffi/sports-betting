from __future__ import annotations

from pathlib import Path

import pandas as pd

from src.config.settings import PATHS, ensure_directories
from src.ingestion.synthetic_data import generate_synthetic_data
from src.utils.io import write_csv
from src.utils.logger import get_logger

logger = get_logger(__name__)


def seed_raw_data(num_matches: int = 280, seed: int = 42) -> tuple[pd.DataFrame, pd.DataFrame]:
    ensure_directories()
    matches_df, bets_df = generate_synthetic_data(num_matches=num_matches, seed=seed)

    write_csv(matches_df, PATHS.raw_dir / "matches_raw.csv")
    write_csv(bets_df, PATHS.raw_dir / "bets_raw.csv")

    sample_matches = matches_df.head(40).copy()
    sample_bets = bets_df.head(60).copy()
    write_csv(sample_matches, PATHS.samples_dir / "sample_matches.csv")
    write_csv(sample_bets, PATHS.samples_dir / "sample_bets.csv")

    logger.info("Seed completed: %s matches | %s bets", len(matches_df), len(bets_df))
    return matches_df, bets_df


def load_raw_data(raw_dir: Path | None = None) -> tuple[pd.DataFrame, pd.DataFrame]:
    source_dir = raw_dir or PATHS.raw_dir
    matches_path = source_dir / "matches_raw.csv"
    bets_path = source_dir / "bets_raw.csv"

    if not matches_path.exists() or not bets_path.exists():
        raise FileNotFoundError("Raw files not found. Run `python -m src.main seed` first.")

    matches_df = pd.read_csv(matches_path)
    bets_df = pd.read_csv(bets_path)
    return matches_df, bets_df
