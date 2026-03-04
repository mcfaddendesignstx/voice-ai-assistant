"""One-time script: drop old memories schema, create thoughts table + match_thoughts (Open Brain)."""
import psycopg2

conn = psycopg2.connect(
    host="aws-0-us-west-2.pooler.supabase.com",
    port=5432,
    dbname="postgres",
    user="postgres.azixybmbgcapvrvwwjmm",
    password="MAtt__041691!",
    sslmode="require",
)
conn.autocommit = True
cur = conn.cursor()

statements = [
    # Clean up old schema
    "DROP TABLE IF EXISTS memories CASCADE;",
    "DROP FUNCTION IF EXISTS match_memories(vector, float, int);",

    # pgvector extension
    "CREATE EXTENSION IF NOT EXISTS vector;",

    # thoughts table — 1536-dim embeddings (text-embedding-3-small via OpenRouter)
    """CREATE TABLE IF NOT EXISTS thoughts (
      id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
      content text NOT NULL,
      embedding vector(1536),
      metadata jsonb DEFAULT '{}',
      created_at timestamptz DEFAULT timezone('utc', now()),
      updated_at timestamptz DEFAULT timezone('utc', now())
    );""",

    # Semantic search RPC
    """CREATE OR REPLACE FUNCTION match_thoughts(
      query_embedding vector(1536),
      match_threshold float DEFAULT 0.5,
      match_count int DEFAULT 5
    )
    RETURNS TABLE (
      id uuid,
      content text,
      metadata jsonb,
      similarity float
    )
    LANGUAGE sql STABLE
    AS $$
      SELECT id, content, metadata,
        1 - (embedding <=> query_embedding) AS similarity
      FROM thoughts
      WHERE 1 - (embedding <=> query_embedding) > match_threshold
      ORDER BY embedding <=> query_embedding
      LIMIT match_count;
    $$;""",

    # Row-level security
    "ALTER TABLE thoughts ENABLE ROW LEVEL SECURITY;",

    # Policy: service_role gets full access
    """DO $$ BEGIN
      IF NOT EXISTS (
        SELECT 1 FROM pg_policies WHERE tablename = 'thoughts' AND policyname = 'Service role full access'
      ) THEN
        CREATE POLICY "Service role full access" ON thoughts FOR ALL USING (auth.role() = 'service_role');
      END IF;
    END $$;""",

    # Also allow anon role (fallback if service_role key not available)
    """DO $$ BEGIN
      IF NOT EXISTS (
        SELECT 1 FROM pg_policies WHERE tablename = 'thoughts' AND policyname = 'Anon full access'
      ) THEN
        CREATE POLICY "Anon full access" ON thoughts FOR ALL USING (true);
      END IF;
    END $$;""",
]

for i, sql in enumerate(statements, 1):
    try:
        cur.execute(sql)
        print(f"[{i}/{len(statements)}] OK")
    except Exception as e:
        print(f"[{i}/{len(statements)}] FAILED: {e}")

cur.close()
conn.close()
print("Schema setup complete.")
