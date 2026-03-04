-- ============================================================
-- Run this in Supabase SQL Editor (Dashboard → SQL Editor → New query)
-- ============================================================

-- 1. Add missing indexes for performance
create index if not exists thoughts_embedding_idx
  on thoughts using hnsw (embedding vector_cosine_ops);

create index if not exists thoughts_metadata_idx
  on thoughts using gin (metadata);

create index if not exists thoughts_created_at_idx
  on thoughts (created_at desc);

-- 2. Auto-update updated_at on row changes
create or replace function update_updated_at()
returns trigger as $$
begin
  new.updated_at = now();
  return new;
end;
$$ language plpgsql;

drop trigger if exists thoughts_updated_at on thoughts;
create trigger thoughts_updated_at
  before update on thoughts
  for each row
  execute function update_updated_at();

-- 3. Replace match_thoughts with Nate's full spec (adds filter param)
create or replace function match_thoughts(
  query_embedding vector(1536),
  match_threshold float default 0.3,
  match_count int default 10,
  filter jsonb default '{}'::jsonb
)
returns table (
  id uuid,
  content text,
  metadata jsonb,
  similarity float,
  created_at timestamptz
)
language plpgsql
as $$
begin
  return query
  select
    t.id,
    t.content,
    t.metadata,
    1 - (t.embedding <=> query_embedding) as similarity,
    t.created_at
  from thoughts t
  where 1 - (t.embedding <=> query_embedding) > match_threshold
    and (filter = '{}'::jsonb or t.metadata @> filter)
  order by t.embedding <=> query_embedding
  limit match_count;
end;
$$;
