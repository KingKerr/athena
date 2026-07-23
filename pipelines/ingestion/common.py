from __future__ import annotations

import os
from pathlib import Path

import duckdb
import pandas as pd

from pipelines.ingestion.massive import MassiveClient


def get_massive_api_key() -> str:
    api_key = os.getenv("MASSIVE_API_KEY")
    if not api_key:
        raise ValueError("MASSIVE_API_KEY is not set.")
    return api_key


def get_duckdb_path() -> str:
    return os.getenv("DUCKDB_PATH", "data/market.duckdb")


def get_duckdb_connection() -> duckdb.DuckDBPyConnection:
    db_path = get_duckdb_path()
    Path(db_path).parent.mkdir(parents=True, exist_ok=True)
    return duckdb.connect(db_path)


def write_dataframe(
    conn: duckdb.DuckDBPyConnection,
    table_name: str,
    df: pd.DataFrame,
    mode: str = "replace",
) -> None:
    if df.empty:
        return

    conn.register("tmp_df", df)

    if mode == "replace":
        conn.execute(f"create or replace table {table_name} as select * from tmp_df")
    elif mode == "append":
        conn.execute(f"insert into {table_name} select * from tmp_df")
    else:
        raise ValueError(f"Unsupported write mode: {mode}")

    conn.unregister("tmp_df")


def build_massive_client() -> MassiveClient:
    return MassiveClient(api_key=get_massive_api_key())