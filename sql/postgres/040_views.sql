CREATE OR REPLACE VIEW v_latest_price_daily AS
SELECT p.*
FROM fact_price_daily p
JOIN (
    SELECT ticker, MAX(date_day) AS max_date_day
    FROM fact_price_daily
    GROUP BY ticker
) latest
  ON p.ticker = latest.ticker
 AND p.date_day = latest.max_date_day;

CREATE OR REPLACE VIEW v_latest_news AS
WITH exploded AS (
    SELECT
        n.news_id,
        n.title,
        n.description,
        n.article_url,
        n.image_url,
        n.author,
        n.published_utc,
        n.publisher_name,
        n.publisher_homepage_url,
        n.publisher_logo_url,
        n.tickers,
        n.keywords,
        n.insights,
        n.raw_json,
        jsonb_array_elements_text(n.tickers) AS ticker
    FROM fact_news n
    WHERE n.tickers IS NOT NULL
),
latest AS (
    SELECT ticker, MAX(published_utc) AS max_published_utc
    FROM exploded
    GROUP BY ticker
)
SELECT e.*
FROM exploded e
JOIN latest l
  ON e.ticker = l.ticker
 AND e.published_utc = l.max_published_utc;

CREATE OR REPLACE VIEW v_latest_filing_sections AS
SELECT f.*
FROM fact_filing_section f
JOIN (
    SELECT ticker, MAX(filing_date) AS max_filing_date
    FROM fact_filing_section
    GROUP BY ticker
) latest
  ON f.ticker = latest.ticker
 AND f.filing_date = latest.max_filing_date;

CREATE OR REPLACE VIEW v_latest_risk_factors AS
SELECT r.*
FROM fact_risk_factor r
JOIN (
    SELECT ticker, MAX(filing_date) AS max_filing_date
    FROM fact_risk_factor
    GROUP BY ticker
) latest
  ON r.ticker = latest.ticker
 AND r.filing_date = latest.max_filing_date;

 CREATE OR REPLACE VIEW v_latest_10k_filing_sections AS
SELECT f.*
FROM fact_filing_section f
JOIN (
    SELECT ticker, MAX(filing_date) AS max_filing_date
    FROM fact_filing_section
    WHERE form_type = '10-K'
    GROUP BY ticker
) latest
  ON f.ticker = latest.ticker
 AND f.filing_date = latest.max_filing_date
WHERE f.form_type = '10-K';


CREATE OR REPLACE VIEW v_latest_10k_risk_factors AS
SELECT r.*
FROM fact_risk_factor r
JOIN (
    SELECT ticker, MAX(filing_date) AS max_filing_date
    FROM fact_risk_factor
    WHERE form_type = '10-K'
    GROUP BY ticker
) latest
  ON r.ticker = latest.ticker
 AND r.filing_date = latest.max_filing_date
WHERE r.form_type = '10-K';


CREATE OR REPLACE VIEW v_rag_10k_context AS
SELECT
    ticker,
    filing_date,
    form_type,
    section_name,
    section_text
FROM fact_filing_section
WHERE form_type = '10-K';


CREATE OR REPLACE VIEW v_rag_10k_risk_context AS
SELECT
    ticker,
    filing_date,
    form_type,
    primary_category,
    supporting_text
FROM fact_risk_factor
WHERE form_type = '10-K';

CREATE OR REPLACE VIEW v_latest_10k_filing_year AS
SELECT
    ticker,
    MAX(EXTRACT(YEAR FROM filing_date))::int AS latest_filing_year,
    MAX(filing_date) AS latest_filing_date
FROM fact_filing_section
WHERE form_type = '10-K'
GROUP BY ticker;

CREATE OR REPLACE VIEW v_rag_chunk_filters AS
SELECT
    chunk_id,
    ticker,
    doc_type,
    doc_id,
    filing_date,
    EXTRACT(YEAR FROM filing_date)::int AS filing_year,
    section_name,
    chunk_order,
    LEFT(chunk_text, 300) AS chunk_preview,
    metadata
FROM rag_chunk;

CREATE OR REPLACE VIEW v_rag_10k_chunks AS
SELECT
    chunk_id,
    ticker,
    doc_type,
    doc_id,
    filing_date,
    EXTRACT(YEAR FROM filing_date)::int AS filing_year,
    section_name,
    chunk_order,
    chunk_text,
    metadata
FROM rag_chunk
WHERE doc_type = '10-K';


CREATE OR REPLACE VIEW v_rag_risk_chunks AS
SELECT
    chunk_id,
    ticker,
    doc_type,
    doc_id,
    filing_date,
    EXTRACT(YEAR FROM filing_date)::int AS filing_year,
    section_name,
    chunk_order,
    chunk_text,
    metadata
FROM rag_chunk
WHERE doc_type = 'risk_factor';