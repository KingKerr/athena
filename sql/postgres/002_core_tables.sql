create table if not exists ticker (
  ticker_id bigserial primary key,
  symbol text not null unique,
  company_name text not null,
  sector text,
  is_active boolean not null default true,
  created_at timestamptz not null default now()
);

create table if not exists source_document (
  document_id bigserial primary key,
  ticker_id bigint not null references ticker(ticker_id),
  source_type text not null,
  source_key text not null unique,
  title text not null,
  published_at timestamptz,
  url text,
  raw_metadata jsonb not null default '{}'::jsonb,
  created_at timestamptz not null default now()
);