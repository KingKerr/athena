import os
from typing import List, Optional, Dict, Any
from openai import OpenAI
from sqlalchemy import create_engine, text


EMBED_MODEL = os.getenv("OPENAI_EMBED_MODEL", "text-embedding-3-small")


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


def embed_query(query_text: str) -> List[float]:
    client = get_client()
    resp = client.embeddings.create(
        model=EMBED_MODEL,
        input=[query_text],
    )
    return resp.data[0].embedding


def retrieve_chunks(
    query_text: str,
    ticker: str,
    year: int,
    doc_types: Optional[List[str]] = None,
    section_name: Optional[str] = None,
    limit: int = 8,
    min_similarity: Optional[float] = None,
) -> List[Dict[str, Any]]:
    if doc_types is None:
        doc_types = ["10-K", "risk_factor"]

    query_embedding = embed_query(query_text)
    engine = get_engine()

    sql = text("""
        SELECT
            chunk_id,
            ticker,
            doc_type,
            doc_id,
            filing_date,
            section_name,
            chunk_order,
            chunk_text,
            1 - (embedding <=> CAST(:query_embedding AS vector)) AS similarity
        FROM rag_chunk
        WHERE ticker = :ticker
          AND EXTRACT(YEAR FROM filing_date) = :year
          AND doc_type = ANY(:doc_types)
          AND (:section_name IS NULL OR section_name = :section_name)
        ORDER BY embedding <=> CAST(:query_embedding AS vector)
        LIMIT :limit
    """)

    with engine.begin() as conn:
        rows = conn.execute(
            sql,
            {
                "ticker": ticker,
                "year": year,
                "doc_types": doc_types,
                "section_name": section_name,
                "query_embedding": str(query_embedding),
                "limit": limit,
            },
        ).mappings().all()
    chunks = [dict(r) for r in rows]
    if min_similarity is not None: 
        chunks = [c for c in chunks if c["similarity"] is not None and c["similarity"] >= min_similarity]
    return chunks 