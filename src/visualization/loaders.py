from __future__ import annotations

from pathlib import Path

import pandas as pd

from src.config.settings import PATHS


def mart_path(table_name: str) -> Path:
    return PATHS.marts_dir / f"{table_name}.csv"


def load_mart(table_name: str) -> pd.DataFrame:
    path = mart_path(table_name)
    if not path.exists():
        return pd.DataFrame()
    return pd.read_csv(path)
