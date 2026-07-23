from __future__ import annotations

import json
from typing import Iterable

import pandas as pd

from pipelines.ingestion.common import build_massive_client, get_duckdb_connection, write_dataframe
from pipelines.ingestion.massive import MassiveFilingsAPI


def ingest_risk_factors(
    tickers: Iterable[str],
    filing_date_gte: str | None = None,
    filing_date_lte: str | None = None,
    limit_per_ticker: int = 100,
) -> pd.DataFrame:
    all_rows: list[dict] = []

    with build_massive_client() as client:
        filings_api = MassiveFilingsAPI(client)

        for ticker in tickers:
            raw_rows = filings_api.get_risk_factors(
                ticker=ticker,
                filing_date_gte=filing_date_gte,
                filing_date_lte=filing_date_lte,
                limit=limit_per_ticker,
            )
            normalized = filings_api.normalize_risk_factors(raw_rows)

            for row in normalized:
                all_rows.append(
                    {
                        "ticker": row["ticker"],
                        "cik": row["cik"],
                        "company_name": row["company_name"],
                        "filing_date": row["filing_date"],
                        "form_type": row["form_type"],
                        "accession_number": row["accession_number"],
                        "primary_category": row["primary_category"],
                        "secondary_category": row["secondary_category"],
                        "tertiary_category": row["tertiary_category"],
                        "supporting_text": row["supporting_text"],
                        "raw_json": json.dumps(row["raw"]),
                    }
                )

    df = pd.DataFrame(all_rows)

    if not df.empty:
        conn = get_duckdb_connection()
        try:
            write_dataframe(conn, "stage_risk_factor", df, mode="replace")
        finally:
            conn.close()

    return df


def ingest_filing_sections(
    tickers: Iterable[str],
    filing_date_gte: str | None = None,
    filing_date_lte: str | None = None,
    form_type: str | None = "10-K",
    limit_per_ticker: int = 100,
) -> pd.DataFrame:
    all_rows: list[dict] = []

    with build_massive_client() as client:
        filings_api = MassiveFilingsAPI(client)

        for ticker in tickers:
            raw_rows = filings_api.get_filing_sections(
                ticker=ticker,
                filing_date_gte=filing_date_gte,
                filing_date_lte=filing_date_lte,
                form_type=form_type,
                limit=limit_per_ticker,
            )
            normalized = filings_api.normalize_filing_sections(raw_rows)

            for row in normalized:
                all_rows.append(
                    {
                        "ticker": row["ticker"],
                        "cik": row["cik"],
                        "company_name": row["company_name"],
                        "filing_date": row["filing_date"],
                        "form_type": row["form_type"],
                        "accession_number": row["accession_number"],
                        "section_name": row["section_name"],
                        "section_text": row["section_text"],
                        "raw_json": json.dumps(row["raw"]),
                    }
                )

    df = pd.DataFrame(all_rows)

    if not df.empty:
        conn = get_duckdb_connection()
        try:
            write_dataframe(conn, "stage_filing_section", df, mode="replace")
        finally:
            conn.close()

    return df


if __name__ == "__main__":
    rf = ingest_risk_factors(
        tickers=["NVDA", "AAPL", "MSFT", "SPOT", "DIS", "NFLX"],
        filing_date_gte="2025-01-01",
        limit_per_ticker=100,
    )
    fs = ingest_filing_sections(
        tickers=["NVDA", "AAPL",  "MSFT", "SPOT", "DIS", "NFLX"],
        filing_date_gte="2025-01-01",
        form_type="10-K",
        limit_per_ticker=100,
    )
    print(f"[ok] staged risk factor rows: {len(rf)}")
    print(f"[ok] staged filing section rows: {len(fs)}")