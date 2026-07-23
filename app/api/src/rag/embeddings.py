import os
import json
import argparse
import hashlib
from typing import List, Dict, Any

from openai import OpenAI
from sqlalchemy import create_engine, text

from src.rag.chunking import chunk_text


EMBED_MODEL = "text-embedding-3-small"

def postgres_url() -> str:
    database_url = os.getenv("DATABASE_URL")
    if database_url:
        if database_url.startswith("postgres://"):
            return database_url.replace("postgres://", "postgresql://", 1)
        return database_url

    return (
        f"postgresql+psycopg2://{os.getenv('POSTGRES_USER')}:"
        f"{os.getenv('POSTGRES_PASSWORD')}@"
        f"{os.getenv('POSTGRES_HOST', 'localhost')}:"
        f"{os.getenv('POSTGRES_PORT', '5432')}/"
        f"{os.getenv('POSTGRES_DB')}"
    )


def get_engine():
    return create_engine(postgres_url(), future=True)

def get_client():
    return OpenAI(api_key=os.getenv("OPENAI_API_KEY"))


def load_filing_sections(engine, ticker: str, year: int) -> List[Dict[str, Any]]:
    sql = text("""
        SELECT
            ticker,
            '10-K' AS doc_type,
            filing_date,
            section_name,
            section_text
        FROM fact_filing_section
        WHERE ticker = :ticker
          AND EXTRACT(YEAR FROM filing_date) = :year
          AND section_text IS NOT NULL
          AND BTRIM(section_text) <> ''
        ORDER BY filing_date, section_name""")
    with engine.begin() as conn:
        rows = conn.execute(sql, {"ticker": ticker, "year": year}).mappings().all()
    out = []
    for r in rows:
        row = dict(r)
        row["doc_id"] = f"{row['ticker']}:10-K:{row['filing_date']}:{row['section_name']}"
        out.append(row)
    return out  


def load_risk_factors(engine, ticker: str, year: int) -> List[Dict[str, Any]]:
    sql = text("""
        SELECT
            ticker,
            'risk_factor' AS doc_type,
            CONCAT(ticker, ':risk_factor:', filing_date, ':', primary_category) AS doc_id,
            filing_date,
            primary_category AS section_name,
            supporting_text AS section_text
        FROM fact_risk_factor
        WHERE ticker = :ticker
          AND EXTRACT(YEAR FROM filing_date) = :year
          AND supporting_text IS NOT NULL
          AND BTRIM(supporting_text) <> ''
        ORDER BY filing_date, primary_category
    """)
    with engine.begin() as conn:
        rows = conn.execute(sql, {"ticker": ticker, "year": year}).mappings().all()
    out = []
    
    for r in rows:
        row = dict(r)
        row["doc_id"] = f"{row['ticker']}:risk_factor:{row['filing_date']}:{row['section_name']}"
        out.append(row)
    return out

def build_chunk_rows(source_rows: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    out = []

    for row in source_rows:
        ticker = row["ticker"]
        doc_type = row["doc_type"]
        doc_id = row["doc_id"]
        filing_date = row["filing_date"]
        section_name = row["section_name"]
        section_text = row["section_text"]
        if doc_type == "risk_factor":
            supporting_hash = hashlib.md5(
                section_text.encode("utf-8")
            ).hexdigest()[:12]
            doc_id = f"{ticker}:risk_factor:{filing_date}:{section_name}:{supporting_hash}"
        else:
            doc_id = row["doc_id"]

        chunks = chunk_text(section_text)

        for i, chunk in enumerate(chunks):
            metadata = {
                "ticker": ticker,
                "doc_type": doc_type,
                "doc_id": doc_id,
                "filing_date": str(filing_date) if filing_date else None,
                "section_name": section_name,
                "chunk_order": i,
            }

            out.append({
                "ticker": ticker,
                "doc_type": doc_type,
                "doc_id": doc_id,
                "filing_date": filing_date,
                "section_name": section_name,
                "chunk_order": i,
                "chunk_text": chunk,
                "metadata": metadata,
            })

    return out


def embed_texts(client: OpenAI, texts: List[str]) -> List[List[float]]:
    if not texts:
        return []

    resp = client.embeddings.create(
        model=EMBED_MODEL,
        input=texts,
    )
    return [item.embedding for item in resp.data]


def upsert_chunks(engine, rows: List[Dict[str, Any]], batch_size: int = 100) -> None:
    if not rows:
        print("[skip] embeddings: no source rows found")
        return

    client = get_client()

    sql = text("""
        INSERT INTO rag_chunk (
            ticker,
            doc_type,
            doc_id,
            filing_date,
            section_name,
            chunk_order,
            chunk_text,
            embedding,
            metadata
        )
        VALUES (
            :ticker,
            :doc_type,
            :doc_id,
            :filing_date,
            :section_name,
            :chunk_order,
            :chunk_text,
            CAST(:embedding AS vector),
            CAST(:metadata AS jsonb)
        )
        ON CONFLICT (ticker, doc_type, doc_id, chunk_order)
        DO UPDATE SET
            filing_date = EXCLUDED.filing_date,
            section_name = EXCLUDED.section_name,
            chunk_text = EXCLUDED.chunk_text,
            embedding = EXCLUDED.embedding,
            metadata = EXCLUDED.metadata
    """)

    total = 0

    for i in range(0, len(rows), batch_size):
        batch = rows[i:i + batch_size]
        texts = [r["chunk_text"] for r in batch]
        embeddings = embed_texts(client, texts)

        payload = []
        for row, embedding in zip(batch, embeddings):
            payload.append({
                "ticker": row["ticker"],
                "doc_type": row["doc_type"],
                "doc_id": row["doc_id"],
                "filing_date": row["filing_date"],
                "section_name": row["section_name"],
                "chunk_order": row["chunk_order"],
                "chunk_text": row["chunk_text"],
                "embedding": str(embedding),
                "metadata": json.dumps(row["metadata"]),
            })

        with engine.begin() as conn:
            conn.execute(sql, payload)

        total += len(payload)
        print(f"[ok] upserted {total} rag chunks so far")

    print(f"[done] embeddings complete: upserted {total} chunks")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--ticker", required=True)
    parser.add_argument("--year", required=True, type=int)
    args = parser.parse_args()

    engine = get_engine()

    filing_rows = load_filing_sections(engine, args.ticker, args.year)
    risk_rows = load_risk_factors(engine, args.ticker, args.year)

    source_rows = filing_rows + risk_rows
    chunk_rows = build_chunk_rows(source_rows)

    print(f"[info] filing rows: {len(filing_rows)}")
    print(f"[info] risk rows: {len(risk_rows)}")
    print(f"[info] chunk rows: {len(chunk_rows)}")

    upsert_chunks(engine, chunk_rows)


if __name__ == "__main__":
    main()