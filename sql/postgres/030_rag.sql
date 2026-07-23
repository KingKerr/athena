CREATE EXTENSION IF NOT EXISTS vector;
CREATE EXTENSION IF NOT EXISTS pgcrypto;
SET search_path TO public, extensions;

CREATE TABLE IF NOT EXISTS rag_chunk (
  chunk_id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  ticker text NOT NULL REFERENCES dim_ticker(ticker),
  doc_type text NOT NULL,
  doc_id text NOT NULL,
  filing_date date,
  section_name text,
  chunk_order integer NOT NULL,
  chunk_text text NOT NULL,
  embedding vector(1536),
  metadata jsonb,
  created_at timestamptz DEFAULT now()
);


CREATE INDEX IF NOT EXISTS idx_rag_chunk_lookup
  ON rag_chunk (ticker, doc_type, filing_date DESC, section_name, chunk_order);


CREATE INDEX IF NOT EXISTS idx_rag_chunk_doc
  ON rag_chunk (doc_id, chunk_order);


CREATE INDEX IF NOT EXISTS idx_rag_chunk_filing_year
  ON rag_chunk (ticker, filing_date DESC);


ALTER TABLE rag_chunk
ADD CONSTRAINT rag_chunk_unique_doc_chunk
UNIQUE (ticker, doc_type, doc_id, chunk_order);