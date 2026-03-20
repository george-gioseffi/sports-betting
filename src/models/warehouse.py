from __future__ import annotations

from pathlib import Path

import duckdb
import pandas as pd


def write_tables_to_duckdb(tables: dict[str, pd.DataFrame], warehouse_path: Path) -> None:
    warehouse_path.parent.mkdir(parents=True, exist_ok=True)
    with duckdb.connect(str(warehouse_path)) as conn:
        for table_name, table_df in tables.items():
            conn.register("tmp_df", table_df)
            conn.execute(f"CREATE OR REPLACE TABLE {table_name} AS SELECT * FROM tmp_df")
            conn.unregister("tmp_df")


def query_duckdb(sql: str, warehouse_path: Path) -> pd.DataFrame:
    with duckdb.connect(str(warehouse_path)) as conn:
        return conn.execute(sql).df()
