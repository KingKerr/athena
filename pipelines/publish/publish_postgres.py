from __future__ import annotations

import json
import os
from typing import Any
import hashlib
import duckdb
import pandas as pd
from sqlalchemy import MetaData, Table, create_engine
from sqlalchemy.dialects.postgresql import JSONB, insert


DUCKDB_PATH = os.getenv("DUCKDB_PATH", "data/market.duckdb")


def postgres_url() -> str:
    user = os.getenv("POSTGRES_USER")
    password = os.getenv("POSTGRES_PASSWORD") or os.getenv("POSTGRES_PASS")
    host = os.getenv("POSTGRES_HOST", "localhost")
    port = os.getenv("POSTGRES_PORT", "5432")
    db = os.getenv("POSTGRES_DB")

    missing = [k for k, v in {
        "POSTGRES_USER": user,
        "POSTGRES_PASSWORD|POSTGRES_PASS": password,
        "POSTGRES_DB": db,
    }.items() if not v]

    if missing:
        raise ValueError(f"Missing Postgres env vars: {', '.join(missing)}")

    return f"postgresql+psycopg2://{user}:{password}@{host}:{port}/{db}"


def get_duckdb_conn() -> duckdb.DuckDBPyConnection:
    return duckdb.connect(DUCKDB_PATH)


def get_engine():
    return create_engine(postgres_url(), future=True)


def fetch_df(conn: duckdb.DuckDBPyConnection, sql: str) -> pd.DataFrame:
    return conn.execute(sql).fetchdf()


def ensure_jsonable(value: Any) -> Any:
    if pd.isna(value):
        return None
    if isinstance(value, str):
        v = value.strip()
        if (v.startswith("{") and v.endswith("}")) or (v.startswith("[") and v.endswith("]")):
            try:
                return json.loads(v)
            except Exception:
                return value
        return value
    if hasattr(value, "tolist"):
        return value.tolist()
    return value


def clean_records(df: pd.DataFrame, json_columns: set[str] | None = None) -> list[dict[str, Any]]:
    json_columns = json_columns or set()
    out: list[dict[str, Any]] = []

    for rec in df.to_dict(orient="records"):
        cleaned: dict[str, Any] = {}
        for key, value in rec.items():
            if key in json_columns:
                cleaned[key] = ensure_jsonable(value)
            else:
                cleaned[key] = None if pd.isna(value) else value
        out.append(cleaned)

    return out


def upsert_table(
    engine,
    table_name: str,
    records: list[dict[str, Any]],
    conflict_cols: list[str],
    update_cols: list[str],
) -> int:
    if not records:
        print(f"[skip] {table_name}: no rows")
        return 0

    metadata = MetaData()
    table = Table(table_name, metadata, autoload_with=engine)
    stmt = insert(table).values(records)

    if update_cols:
        set_map = {col: getattr(stmt.excluded, col) for col in update_cols}
        stmt = stmt.on_conflict_do_update(
            index_elements=conflict_cols,
            set_=set_map,
        )
    else:
        stmt = stmt.on_conflict_do_nothing(
            index_elements=conflict_cols,
        )

    with engine.begin() as conn:
        conn.execute(stmt)

    print(f"[ok] {table_name}: upserted {len(records)} rows")
    return len(records)


def publish_dim_ticker(dconn, engine) -> int:
    df = fetch_df(dconn, """
        select distinct
            upper(ticker) as ticker,
            company_name,
            cik,
            exchange,
            sector,
            industry
        from mart_dim_ticker
        where ticker is not null
    """)
    records = clean_records(df)
    return upsert_table(
        engine,
        "dim_ticker",
        records,
        conflict_cols=["ticker"],
        update_cols=["company_name", "cik", "exchange", "sector", "industry"],
    )


def publish_dim_date(dconn, engine) -> int:
    df = fetch_df(dconn, """
        select distinct
            date_day
        from mart_dim_date
        where date_day is not null
    """)
    records = clean_records(df)
    return upsert_table(
        engine,
        "dim_date",
        records,
        conflict_cols=["date_day"],
        update_cols=[],
    ) if records else 0


def backfill_dim_ticker_from_facts(dconn, engine) -> int:
    df = fetch_df(dconn, """
        with all_tickers as (
            select distinct upper(ticker) as ticker from mart_fact_price_daily where ticker is not null
            union
            select distinct upper(ticker) as ticker from mart_fact_news, unnest(string_split(replace(replace(tickers, '[', ''), ']', ''), ',')) t(ticker)
            where tickers is not null
            union
            select distinct upper(ticker) as ticker from mart_fact_filing_section where ticker is not null
            union
            select distinct upper(ticker) as ticker from mart_fact_risk_factor where ticker is not null
        )
        select ticker
        from all_tickers
        where ticker is not null and ticker <> ''
    """)
    records = clean_records(df)
    return upsert_table(
        engine,
        "dim_ticker",
        records,
        conflict_cols=["ticker"],
        update_cols=[],
    ) if records else 0


def backfill_dim_date_from_facts(dconn, engine) -> int:
    df = fetch_df(dconn, """
        with all_dates as (
            select distinct cast(to_timestamp(ts_ms / 1000) as date) as date_day
            from mart_fact_price_daily
            where ts_ms is not null
            union
            select distinct cast(published_utc as date) as date_day
            from mart_fact_news
            where published_utc is not null
            union
            select distinct cast(filing_date as date) as date_day
            from mart_fact_filing_section
            where filing_date is not null
            union
            select distinct cast(filing_date as date) as date_day
            from mart_fact_risk_factor
            where filing_date is not null
        )
        select date_day
        from all_dates
        where date_day is not null
    """)
    records = clean_records(df)
    return upsert_table(
        engine,
        "dim_date",
        records,
        conflict_cols=["date_day"],
        update_cols=[],
    ) if records else 0


def publish_fact_price_daily(dconn, engine) -> int:
    df = fetch_df(dconn, """
        select
            upper(ticker) as ticker,
            cast(to_timestamp(ts_ms / 1000) as date) as date_day,
            open,
            high,
            low,
            close,
            volume,
            vwap,
            transactions
        from mart_fact_price_daily
        where ticker is not null
          and ts_ms is not null
    """)
    records = clean_records(df)
    return upsert_table(
        engine,
        "fact_price_daily",
        records,
        conflict_cols=["ticker", "date_day"],
        update_cols=["open", "high", "low", "close", "volume", "vwap", "transactions"],
    )


def publish_fact_news(dconn, engine) -> int:
    df = fetch_df(dconn, """
        select
            news_id,
            title,
            description,
            article_url,
            image_url,
            author,
            published_utc,
            publisher_name,
            publisher_homepage_url,
            publisher_logo_url,
            tickers,
            keywords,
            insights,
            raw_json
        from mart_fact_news
        where news_id is not null
    """)
    records = clean_records(df, json_columns={"tickers", "keywords", "insights", "raw_json"})
    return upsert_table(
        engine,
        "fact_news",
        records,
        conflict_cols=["news_id"],
        update_cols=[
            "title",
            "description",
            "article_url",
            "image_url",
            "author",
            "published_utc",
            "publisher_name",
            "publisher_homepage_url",
            "publisher_logo_url",
            "tickers",
            "keywords",
            "insights",
            "raw_json",
        ],
    )

def _sha256_text(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()

def publish_fact_filing_section(dconn, engine) -> int:
    df = fetch_df(dconn, """
        select
            upper(ticker) as ticker,
            cik,
            company_name,
            filing_date,
            form_type,
            accession_number,
            section_name,
            section_text,
            raw_json
        from mart_fact_filing_section
        where ticker is not null
    """)
    print("fact_filing_section df rows:", len(df), "columns:", list(df.columns))
    df["section_hash"] = df["section_text"].fillna("").map(_sha256_text)
    records = clean_records(df, json_columns={"raw_json"})
    print("fact_filing_section records:", len(records))
    return upsert_table(
        engine,
        "fact_filing_section",
        records,
        conflict_cols=["ticker", "filing_date", "section_hash"],
        update_cols=[
            "cik",
            "company_name",
            "form_type",
            "section_text",
            "raw_json",
        ],
    )

def _risk_factor_key(row) -> str:
    parts = [
        row.get("primary_category") or "",
        row.get("secondary_category") or "",
        row.get("tertiary_category") or "",
        row.get("supporting_text") or "",
    ]
    return _sha256_text("|".join(parts))

def publish_fact_risk_factor(dconn, engine) -> int:
    df = fetch_df(dconn, """
        select
            upper(ticker) as ticker,
            cik,
            company_name,
            filing_date,
            form_type,
            accession_number,
            primary_category,
            secondary_category,
            tertiary_category,
            supporting_text,
            raw_json
        from mart_fact_risk_factor
        where ticker is not null
    """)
    df["risk_factor_hash"] = df.apply(_risk_factor_key, axis=1)
    print("fact_risk_factor df rows:", len(df), "columns:", list(df.columns))
    records = clean_records(df, json_columns={"raw_json"})
    print("fact_risk_factor records:", len(records))
    return upsert_table(
        engine,
        "fact_risk_factor",
        records,
        conflict_cols=["ticker", "filing_date", "risk_factor_hash"],
        update_cols=[
            "cik",
            "company_name",
            "form_type",
            "secondary_category", 
            "tertiary_category",
            "supporting_text",
            "raw_json",
        ],
    )


def main() -> None:
    dconn = get_duckdb_conn()
    engine = get_engine()

    try:
        publish_dim_ticker(dconn, engine)
        publish_dim_date(dconn, engine)
        backfill_dim_ticker_from_facts(dconn, engine)
        backfill_dim_date_from_facts(dconn, engine)

        publish_fact_price_daily(dconn, engine)
        publish_fact_news(dconn, engine)
        publish_fact_filing_section(dconn, engine)
        publish_fact_risk_factor(dconn, engine)

        print("Postgres publish complete.")
    finally:
        dconn.close()


if __name__ == "__main__":
    main()