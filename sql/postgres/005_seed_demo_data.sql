/* Will remove this... Not needed */
insert into ticker (symbol, company_name, sector)
values
  ('NVDA', 'NVIDIA Corporation', 'Semiconductors'),
  ('AAPL', 'Apple Inc.', 'Consumer Electronics'),
  ('MSFT', 'Microsoft Corporation', 'Software')
on conflict (symbol) do update
set
  company_name = excluded.company_name,
  sector = excluded.sector;

with docs as (
  insert into source_document (
    ticker_id,
    source_type,
    source_key,
    title,
    published_at,
    url,
    raw_metadata
  )
  values
    (
      (select ticker_id from ticker where symbol = 'NVDA'),
      'news',
      'seed:nvda:earnings:001',
      'NVIDIA demand remains strong across AI infrastructure',
      '2026-06-01T12:00:00Z',
      'https://example.com/nvda-demand',
      '{"publisher":"seed","theme":"ai-demand"}'::jsonb
    ),
    (
      (select ticker_id from ticker where symbol = 'AAPL'),
      'news',
      'seed:aapl:services:001',
      'Apple services growth offsets hardware variability',
      '2026-05-28T12:00:00Z',
      'https://example.com/aapl-services',
      '{"publisher":"seed","theme":"services-growth"}'::jsonb
    ),
    (
      (select ticker_id from ticker where symbol = 'MSFT'),
      'news',
      'seed:msft:cloud:001',
      'Microsoft cloud expansion continues with enterprise AI demand',
      '2026-05-30T12:00:00Z',
      'https://example.com/msft-cloud',
      '{"publisher":"seed","theme":"cloud-ai"}'::jsonb
    )
  on conflict (source_key) do update
  set
    title = excluded.title,
    published_at = excluded.published_at,
    url = excluded.url,
    raw_metadata = excluded.raw_metadata
  returning document_id, source_key
)
insert into document_chunk (
  document_id,
  chunk_order,
  chunk_text,
  token_count,
  chunk_metadata
)
values
  (
    (select document_id from source_document where source_key = 'seed:nvda:earnings:001'),
    0,
    'NVIDIA continued to benefit from strong data center demand tied to AI training and inference workloads. Management highlighted sustained infrastructure spending by large enterprise and cloud customers.',
    29,
    '{"section":"summary"}'::jsonb
  ),
  (
    (select document_id from source_document where source_key = 'seed:nvda:earnings:001'),
    1,
    'Key watch items include supply constraints, concentration in hyperscale demand, and sensitivity to shifts in capital expenditure by a small number of very large buyers.',
    27,
    '{"section":"risks"}'::jsonb
  ),
  (
    (select document_id from source_document where source_key = 'seed:aapl:services:001'),
    0,
    'Apple services revenue remained a stabilizing factor, helping offset uneven device upgrade cycles. Recurring subscriptions and ecosystem lock-in continue to support margins.',
    25,
    '{"section":"summary"}'::jsonb
  ),
  (
    (select document_id from source_document where source_key = 'seed:aapl:services:001'),
    1,
    'Key watch items include regulatory pressure on platform economics, dependency on premium consumer spending, and slower hardware replacement cycles in mature markets.',
    25,
    '{"section":"risks"}'::jsonb
  ),
  (
    (select document_id from source_document where source_key = 'seed:msft:cloud:001'),
    0,
    'Microsoft saw continued momentum in cloud and enterprise AI adoption, with customers expanding usage across productivity, infrastructure, and developer workflows.',
    23,
    '{"section":"summary"}'::jsonb
  ),
  (
    (select document_id from source_document where source_key = 'seed:msft:cloud:001'),
    1,
    'Key watch items include cloud margin pressure, enterprise budget sensitivity, and execution risk as AI product demand grows across a wide portfolio.',
    23,
    '{"section":"risks"}'::jsonb
  )
on conflict (document_id, chunk_order) do update
set
  chunk_text = excluded.chunk_text,
  token_count = excluded.token_count,
  chunk_metadata = excluded.chunk_metadata;