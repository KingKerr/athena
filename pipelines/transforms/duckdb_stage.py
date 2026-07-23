from __future__ import annotations

import os
from pathlib import Path

import duckdb


DUCKDB_PATH = os.getenv("DUCKDB_PATH", "data/market.duckdb")

SQL_FILES = [
    "sql/duckdb/stage/stage_prices.sql",
    "sql/duckdb/stage/stage_news.sql",
    "sql/duckdb/stage/stage_filings.sql",
    "sql/duckdb/intermediate/features.sql",
    "sql/duckdb/marts/mart_dimensions.sql",
    "sql/duckdb/marts/mart_facts.sql",
]


def ensure_parent_dir(db_path: str) -> None:
    Path(db_path).parent.mkdir(parents=True, exist_ok=True)


def run_sql_file(conn: duckdb.DuckDBPyConnection, sql_path: str) -> None:
    path = Path(sql_path)
    if not path.exists():
        raise FileNotFoundError(f"SQL file not found: {sql_path}")

    sql_text = path.read_text(encoding="utf-8").strip()
    if not sql_text:
        print(f"[skip] empty SQL file: {sql_path}")
        return

    conn.execute(sql_text)
    print(f"[ok] ran {sql_path}")


def main() -> None:
    ensure_parent_dir(DUCKDB_PATH)
    conn = duckdb.connect(DUCKDB_PATH)

    try:
        for sql_path in SQL_FILES:
            run_sql_file(conn, sql_path)

        print(f"[ok] DuckDB build complete: {DUCKDB_PATH}")
    finally:
        conn.close()


if __name__ == "__main__":
    main()