create or replace table mart_fact_price_daily as
select
    upper(ticker) as ticker,
    ts_ms,
    open,
    high,
    low,
    close,
    volume,
    vwap,
    transactions,
    otc,
    raw as raw_json
from stage_price_daily
where ticker is not null
  and ts_ms is not null
;

create or replace table mart_fact_news as
select distinct
    news_id,
    title,
    description,
    article_url,
    image_url,
    author,
    cast(published_utc as timestamp) as published_utc,
    publisher_name,
    publisher_homepage_url,
    publisher_logo_url,
    tickers,
    keywords,
    insights,
    raw_json
from stage_news
where news_id is not null
;

  -- Fact: filing sections mart (no accession_number filter)

CREATE OR REPLACE TABLE mart_fact_filing_section AS
SELECT DISTINCT
    upper(ticker) AS ticker,
    cik,
    company_name,
    CAST(filing_date AS DATE) AS filing_date,
    form_type,
    accession_number,
    section_name,
    section_text,
    raw_json
FROM stage_filing_section
WHERE ticker IS NOT NULL;
  -- removed accession_number/section_name/section_text filters

-- Fact: risk factors mart (no accession_number filter)

CREATE OR REPLACE TABLE mart_fact_risk_factor AS
SELECT DISTINCT
    upper(ticker) AS ticker,
    cik,
    company_name,
    CAST(filing_date AS DATE) AS filing_date,
    form_type,
    accession_number,
    primary_category,
    secondary_category,
    tertiary_category,
    supporting_text,
    raw_json
FROM stage_risk_factor
WHERE ticker IS NOT NULL;
  -- removed accession_number/primary_category/supporting_text filters