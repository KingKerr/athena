from sqlalchemy import text
from sqlalchemy.orm import Session


def retrieve_chunks(db: Session, ticker: str, query_text: str, top_k: int = 6) -> list[dict]:
    sql = text(
        """
        select
            sd.document_id,
            sd.title,
            sd.url,
            sd.published_at,
            dc.chunk_id,
            dc.chunk_order,
            dc.chunk_text,
            0.0 as score
        from source_document sd
        join ticker t
          on t.ticker_id = sd.ticker_id
        join document_chunk dc
          on dc.document_id = sd.document_id
        where t.symbol = :ticker
        order by sd.published_at desc nulls last, dc.chunk_order asc
        limit :top_k
        """
    )

    rows = db.execute(sql, {"ticker": ticker.upper(), "top_k": top_k}).mappings().all()
    return [dict(r) for r in rows]