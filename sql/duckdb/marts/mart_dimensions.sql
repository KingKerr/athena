create or replace table mart_dim_ticker as
with ticker_union as (
    select distinct
        upper(ticker) as ticker,
        null::varchar as company_name,
        null::varchar as cik,
        null::varchar as exchange,
        null::varchar as sector,
        null::varchar as industry
    from stage_price_daily
    where ticker is not null

    union

    select distinct
        upper(ticker) as ticker,
        company_name,
        cik,
        null::varchar as exchange,
        null::varchar as sector,
        null::varchar as industry
    from stage_filing_section
    where ticker is not null

    union

    select distinct
        upper(ticker) as ticker,
        company_name,
        cik,
        null::varchar as exchange,
        null::varchar as sector,
        null::varchar as industry
    from stage_risk_factor
    where ticker is not null
),
ranked as (
    select
        ticker,
        company_name,
        cik,
        exchange,
        sector,
        industry,
        row_number() over (
            partition by ticker
            order by
                case when company_name is not null then 0 else 1 end,
                case when cik is not null then 0 else 1 end
        ) as rn
    from ticker_union
)
select
    ticker,
    company_name,
    cik,
    exchange,
    sector,
    industry
from ranked
where rn = 1
;

create or replace table mart_dim_date as
with observed_dates as (
    select cast(to_timestamp(ts_ms / 1000) as date) as date_day
    from stage_price_daily
    where ts_ms is not null

    union

    select cast(published_utc as date) as date_day
    from stage_news
    where published_utc is not null

    union

    select cast(filing_date as date) as date_day
    from stage_filing_section
    where filing_date is not null

    union

    select cast(filing_date as date) as date_day
    from stage_risk_factor
    where filing_date is not null
),
bounds as (
    select
        min(date_day) as min_date,
        max(date_day) as max_date
    from observed_dates
),
series as (
    select
        unnest(generate_series(min_date, max_date, interval '1 day'))::date as date_day
    from bounds
    where min_date is not null and max_date is not null
)
select
    date_day
from series
;