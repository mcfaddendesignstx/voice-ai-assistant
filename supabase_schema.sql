-- ═══════════════════════════════════════════════════════════════
-- Voice AI Agent — Open Brain Memory Schema (pgvector, 1536-dim)
-- Based on Nate B. Jones's "Open Brain" architecture.
-- Run this in the Supabase SQL Editor (Dashboard → SQL Editor → New query)
-- ═══════════════════════════════════════════════════════════════

create extension if not exists vector;

create table if not exists thoughts (
  id uuid primary key default gen_random_uuid(),
  content text not null,
  embedding vector(1536),
  metadata jsonb default '{}',
  created_at timestamptz default timezone('utc', now()),
  updated_at timestamptz default timezone('utc', now())
);

create or replace function match_thoughts(
  query_embedding vector(1536),
  match_threshold float default 0.5,
  match_count int default 5
)
returns table (
  id uuid,
  content text,
  metadata jsonb,
  similarity float
)
language sql stable
as $$
  select id, content, metadata,
    1 - (embedding <=> query_embedding) as similarity
  from thoughts
  where 1 - (embedding <=> query_embedding) > match_threshold
  order by embedding <=> query_embedding
  limit match_count;
$$;

alter table thoughts enable row level security;

create policy "Service role full access"
  on thoughts for all
  using (auth.role() = 'service_role');
