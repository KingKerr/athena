CREATE TABLE IF NOT EXISTS dim_ticker (
    ticker        VARCHAR PRIMARY KEY,
    company_name  VARCHAR,
    cik           VARCHAR,
    exchange      VARCHAR,
    sector        VARCHAR,
    industry      VARCHAR
);

CREATE TABLE IF NOT EXISTS dim_date (
    date_day      DATE PRIMARY KEY
);