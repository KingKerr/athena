from __future__ import annotations

import json
from typing import Iterable

import pandas as pd

from pipelines.ingestion.common import build_massive_client, get_duckdb_connection, write_dataframe
from pipelines.ingestion.massive import MassiveNewsAPI


def ingest_news(
    tickers: Iterable[str],
    published_utc_gte: str | None = None,
    published_utc_lte: str | None = None,
    limit_per_ticker: int = 100,
) -> pd.DataFrame:
    all_rows: list[dict] = []

    with build_massive_client() as client:
        news_api = MassiveNewsAPI(client)

        for ticker in tickers:
            raw_rows = news_api.get_ticker_news(
                ticker=ticker,
                published_utc_gte=published_utc_gte,
                published_utc_lte=published_utc_lte,
                limit=limit_per_ticker,
            )
            normalized = news_api.normalize_news(raw_rows)

            for row in normalized:
                all_rows.append(
                    {
                        "ticker_request": ticker,
                        "news_id": row["news_id"],
                        "title": row["title"],
                        "description": row["description"],
                        "article_url": row["article_url"],
                        "image_url": row["image_url"],
                        "author": row["author"],
                        "published_utc": row["published_utc"],
                        "publisher_name": row["publisher_name"],
                        "publisher_homepage_url": row["publisher_homepage_url"],
                        "publisher_logo_url": row["publisher_logo_url"],
                        "tickers": json.dumps(row["tickers"]),
                        "keywords": json.dumps(row["keywords"]),
                        "insights": json.dumps(row["insights"]),
                        "raw_json": json.dumps(row["raw"]),
                    }
                )

    df = pd.DataFrame(all_rows)

    if not df.empty:
        conn = get_duckdb_connection()
        try:
            write_dataframe(conn, "stage_news", df, mode="replace")
        finally:
            conn.close()

    return df


if __name__ == "__main__":
    df = ingest_news(
        tickers=["NVDA", "AAPL", "MSFT", "NFLX"],
        published_utc_gte="2026-05-01",
        limit_per_ticker=50,
    )
    print(f"[ok] staged news rows: {len(df)}")