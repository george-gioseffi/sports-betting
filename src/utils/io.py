from __future__ import annotations

from pathlib import Path

import pandas as pd


def write_csv(df: pd.DataFrame, path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(path, index=False)


def read_csv(path: Path) -> pd.DataFrame:
    return pd.read_csv(path)


def write_tables_to_csv(tables: dict[str, pd.DataFrame], output_dir: Path) -> None:
    output_dir.mkdir(parents=True, exist_ok=True)
    for table_name, table_df in tables.items():
        table_df.to_csv(output_dir / f"{table_name}.csv", index=False)
