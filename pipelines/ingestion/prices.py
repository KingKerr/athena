from __future__ import annotations

from typing import Iterable

import pandas as pd

from pipelines.ingestion.common import build_massive_client, get_duckdb_connection, write_dataframe
from pipelines.ingestion.massive import MassiveAggsAPI


def ingest_daily_prices(
    tickers: Iterable[str],
    from_date: str,
    to_date: str,
    adjusted: bool = True,
) -> pd.DataFrame:
    all_rows: list[dict] = []

    with build_massive_client() as client:
        aggs_api = MassiveAggsAPI(client)

        for ticker in tickers:
            raw_rows = aggs_api.get_daily_bars(
                ticker=ticker,
                from_date=from_date,
                to_date=to_date,
                adjusted=adjusted,
            )
            normalized = aggs_api.normalize_bars(raw_rows, ticker=ticker)
            all_rows.extend(normalized)

    df = pd.DataFrame(all_rows)
    print("[debug] prices df shape:", df.shape)
    print("[debug] prices df head:", df.head(3))
    if not df.empty:
        conn = get_duckdb_connection()
        try:
            write_dataframe(conn, "stage_price_daily", df, mode="replace")
        finally:
            conn.close()
    
    return df


if __name__ == "__main__":
    df = ingest_daily_prices(
        tickers=["NVDA", "AAPL", "MSFT", "SPOT", "DIS", "NFLX"],
        from_date="2026-05-01",
        to_date="2026-06-13",
    )
    print(f"[ok] staged price rows: {len(df)}")