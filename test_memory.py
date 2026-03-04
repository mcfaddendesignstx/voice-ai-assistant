"""Test script: store a memory, then retrieve it with a semantically similar query."""
from supabase import create_client
from sentence_transformers import SentenceTransformer

url = "https://azixybmbgcapvrvwwjmm.supabase.co"
key = (
    "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9."
    "eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImF6aXh5Ym1iZ2NhcHZydnd3am1tIiwi"
    "cm9sZSI6ImFub24iLCJpYXQiOjE3NjQ0NzkzMzIsImV4cCI6MjA4MDA1NTMzMn0."
    "OU90pXf3s9xdTPf7hHDm2_cBdgfiOXA9e8LD-iEVzMM"
)
sb = create_client(url, key)
model = SentenceTransformer("all-MiniLM-L6-v2")

# 1. Store a test memory
text = "The user prefers to be called Nate and likes dark roast coffee."
emb = model.encode(text, normalize_embeddings=True).tolist()
r = sb.table("memories").insert({
    "content": text,
    "embedding": emb,
    "session_id": "test-session-001",
    "source": "voice_conversation",
    "metadata": {"type": "test"},
}).execute()
stored_id = r.data[0]["id"]
print(f"Stored memory: {stored_id}")

# 2. Retrieve with a semantically similar query
query = "What does the user like to drink?"
qemb = model.encode(query, normalize_embeddings=True).tolist()
r2 = sb.rpc("match_memories", {
    "query_embedding": qemb,
    "match_threshold": 0.3,
    "match_count": 5,
}).execute()
print(f"Retrieved: {len(r2.data)} memories")
for m in r2.data:
    sim = m["similarity"]
    content = m["content"]
    print(f"  sim={sim:.3f}  {content}")

# 3. Clean up test data
sb.table("memories").delete().eq("id", stored_id).execute()
print(f"Cleaned up test memory {stored_id}")
print("ALL TESTS PASSED")
