SET search_path TO public, extensions;
create table if not exists document_chunk (
  chunk_id bigserial primary key,
  document_id bigint not null references source_document(document_id) on delete cascade,
  chunk_order int not null,
  chunk_text text not null,
  token_count int,
  embedding vector(1536),
  chunk_metadata jsonb not null default '{}'::jsonb,
  created_at timestamptz not null default now(),
  unique (document_id, chunk_order)
);