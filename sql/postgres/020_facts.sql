CREATE TABLE IF NOT EXISTS fact_price_daily (
    ticker        VARCHAR NOT NULL,
    date_day      DATE    NOT NULL,
    open          DOUBLE PRECISION,
    high          DOUBLE PRECISION,
    low           DOUBLE PRECISION,
    close         DOUBLE PRECISION,
    volume        BIGINT,
    vwap          DOUBLE PRECISION,
    transactions  BIGINT,
    PRIMARY KEY (ticker, date_day)
);

CREATE TABLE IF NOT EXISTS fact_news (
    news_id                 VARCHAR PRIMARY KEY,
    title                   TEXT,
    description             TEXT,
    article_url             TEXT,
    image_url               TEXT,
    author                  TEXT,
    published_utc           TIMESTAMP,
    publisher_name          TEXT,
    publisher_homepage_url  TEXT,
    publisher_logo_url      TEXT,
    tickers                 JSONB,
    keywords                JSONB,
    insights                JSONB,
    raw_json                JSONB
);

CREATE TABLE fact_risk_factor (
    ticker             VARCHAR NOT NULL,
    cik                VARCHAR,
    company_name       VARCHAR,
    filing_date        DATE NOT NULL,
    form_type          VARCHAR,
    accession_number   VARCHAR,
    primary_category   VARCHAR,
    secondary_category VARCHAR,
    tertiary_category  VARCHAR,
    supporting_text    TEXT,
    risk_factor_hash   VARCHAR NOT NULL,
    raw_json           JSONB,
    PRIMARY KEY (
        ticker,
        filing_date,
        risk_factor_hash
    )
);

CREATE TABLE fact_filing_section (
    ticker            VARCHAR NOT NULL,
    cik               VARCHAR,
    company_name      VARCHAR,
    filing_date       DATE NOT NULL,
    form_type         VARCHAR,
    accession_number  VARCHAR,
    section_name      VARCHAR,
    section_text      TEXT NOT NULL,
    section_hash      VARCHAR NOT NULL,
    raw_json          JSONB,
    PRIMARY KEY (
        ticker,
        filing_date,
        section_hash
    )
);