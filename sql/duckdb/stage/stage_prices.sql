create table if not exists stage_price_daily (
  ticker text,
  ts_ms bigint,
  open double,
  high double,
  low double,
  close double,
  volume double,
  vwap double,
  transactions bigint,
  otc boolean,
  raw json
);