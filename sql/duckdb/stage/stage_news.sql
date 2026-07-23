create table if not exists stage_news (
  ticker_request text,
  news_id text,
  title text,
  description text,
  article_url text,
  image_url text,
  author text,
  published_utc timestamptz,
  publisher_name text,
  publisher_homepage_url text,
  publisher_logo_url text,
  tickers text,
  keywords text,
  insights text,
  raw_json text
);