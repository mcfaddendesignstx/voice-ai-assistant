Now we’re working from Nate’s actual documentation. This changes the prompt significantly. Let me rewrite it properly.
Key differences from what I gave you before:
	∙	Nate uses OpenRouter as the AI gateway, not direct API calls
	∙	His embeddings are 1536-dimensional (text-embedding-3-small via OpenRouter) — NOT 384. My earlier prompt had this wrong
	∙	The Edge Function handles both embedding AND metadata extraction in parallel server-side
	∙	His table is called thoughts not memories
	∙	His search function is match_thoughts not match_memories
	∙	The MCP server is a second Edge Function (open-brain-mcp) with 4 tools: search, browse recent, stats, capture
	∙	Authentication uses a ?key= URL parameter or x-brain-key header
Here’s the corrected Windsurf prompt:

WINDSURF PROMPT — COPY THIS ENTIRE BLOCK:

You are integrating Nate B. Jones’s “Open Brain” persistent vector memory system into an existing voice AI agent running on this Windows workstation. This is a precisely documented architecture — follow it exactly. Do not improvise or substitute components.

STEP 1 — RECONNAISSANCE (DO THIS FIRST, NO EXCEPTIONS)
Find the voice agent project:
	∙	Search all drives and common locations for the active voice agent project. Look for Python files containing any of these keywords: elevenlabs, gemma, pipecat, livekit, voice, agent, tts, stt. Check Desktop, Documents, Downloads, and any folder named after a project.
	∙	Read every relevant Python file completely. Understand the full architecture — how STT works, how Gemma 3 Flash Preview is being called (what API endpoint, what parameters), how ElevenLabs TTS is called, how the conversation loop runs, what the system prompt looks like, and what framework is in use.
	∙	Identify the exact entry point file, requirements.txt or pyproject.toml, and any existing .env file.
Find existing Supabase credentials:
	∙	Search ALL workspace folders, recent project directories, .env files, config files, and any file named supabase, .env, config, secrets, or credentials for a Supabase project URL, anon key, or service role key.
	∙	Also search for any OpenRouter API key already on this machine.
	∙	When you find credentials, use them. Do not ask the user for credentials that already exist on this machine.
	∙	Report exactly what you found and where before proceeding.
What you are NOT changing:
	∙	The existing voice pipeline (STT → LLM → TTS) must continue working exactly as it does now
	∙	Gemma 3 Flash Preview stays as the LLM
	∙	ElevenLabs stays as TTS
	∙	The existing framework stays in place
	∙	You are ADDING memory retrieval as a layer, not rebuilding the agent

STEP 2 — WHAT YOU ARE BUILDING
You are implementing Nate B. Jones’s “Open Brain” architecture from his guide “Your Second Brain Is Closed. Your AI Can’t Use It. Here’s the Fix.” The exact architecture:
Storage: Supabase PostgreSQL with pgvector extension
Embeddings: OpenRouter → text-embedding-3-small → 1536 dimensions
Metadata extraction: OpenRouter → gpt-4o-mini (runs in parallel with embedding, server-side)
Retrieval: Supabase RPC function match_thoughts using vector cosine similarity
Table name: thoughts (not memories, not documents — exactly thoughts)
Cost: ~$0.10–0.30/month at 20 captures/day

STEP 3 — SUPABASE DATABASE SETUP
Using the Supabase credentials found in Step 1, execute the following SQL in the Supabase SQL Editor:
Enable pgvector:
In Supabase dashboard → Database → Extensions → search “vector” → enable pgvector.
Create thoughts table:

create table if not exists thoughts (
  id uuid primary key default gen_random_uuid(),
  content text not null,
  embedding vector(1536),
  metadata jsonb default '{}',
  created_at timestamptz default timezone('utc', now()),
  updated_at timestamptz default timezone('utc', now())
);


Create semantic search function:

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
  select
    id,
    content,
    metadata,
    1 - (embedding <=> query_embedding) as similarity
  from thoughts
  where 1 - (embedding <=> query_embedding) > match_threshold
  order by embedding <=> query_embedding
  limit match_count;
$$;


Row Level Security:

alter table thoughts enable row level security;

create policy "Service role full access"
  on thoughts
  for all
  using (auth.role() = 'service_role');


Verify: Table Editor should show thoughts table with columns: id, content, embedding, metadata, created_at, updated_at. Database → Functions should show match_thoughts.

STEP 4 — OPENROUTER SETUP
You need an OpenRouter API key. Check if one already exists on this machine (found in Step 1). If not found, the user will need to create one at openrouter.ai/keys — tell them to do this and paste it into the .env file.
OpenRouter is used for:
	∙	Embeddings: openai/text-embedding-3-small — 1536 dimensions, ~$0.02/million tokens
	∙	Metadata extraction: openai/gpt-4o-mini — classifies thought type, extracts people and action items

STEP 5 — BUILD THE MEMORY MANAGER
Create memory_manager.py in the project root. This class handles all memory operations without touching the voice pipeline:

import asyncio
import json
import uuid
from datetime import datetime
from typing import Optional
import httpx
from supabase import create_client, Client
import os

class MemoryManager:
    def __init__(self):
        self.supabase: Client = create_client(
            os.environ["SUPABASE_URL"],
            os.environ["SUPABASE_SERVICE_ROLE_KEY"]
        )
        self.openrouter_key = os.environ["OPENROUTER_API_KEY"]
        self.embedding_model = "openai/text-embedding-3-small"
        self.metadata_model = "openai/gpt-4o-mini"
        self.match_threshold = float(os.environ.get("MEMORY_MATCH_THRESHOLD", "0.5"))
        self.match_count = int(os.environ.get("MEMORY_MATCH_COUNT", "5"))
        self.enabled = os.environ.get("MEMORY_ENABLED", "true").lower() == "true"

    async def get_embedding(self, text: str) -> list[float]:
        """Generate 1536-dim embedding via OpenRouter."""
        async with httpx.AsyncClient() as client:
            response = await client.post(
                "https://openrouter.ai/api/v1/embeddings",
                headers={
                    "Authorization": f"Bearer {self.openrouter_key}",
                    "Content-Type": "application/json"
                },
                json={
                    "model": self.embedding_model,
                    "input": text
                },
                timeout=10.0
            )
            response.raise_for_status()
            return response.json()["data"][0]["embedding"]

    async def extract_metadata(self, content: str) -> dict:
        """Extract structured metadata via gpt-4o-mini — runs in parallel with embedding."""
        async with httpx.AsyncClient() as client:
            response = await client.post(
                "https://openrouter.ai/api/v1/chat/completions",
                headers={
                    "Authorization": f"Bearer {self.openrouter_key}",
                    "Content-Type": "application/json"
                },
                json={
                    "model": self.metadata_model,
                    "messages": [{
                        "role": "user",
                        "content": f"""Extract metadata from this thought. Return ONLY valid JSON with these fields:
- type: one of [person_note, decision, insight, meeting_debrief, ai_save, general]
- topics: array of topic strings
- people: array of person names mentioned
- action_items: array of action items if any

Thought: {content}

JSON only, no explanation:"""
                    }],
                    "temperature": 0.1
                },
                timeout=10.0
            )
            response.raise_for_status()
            raw = response.json()["choices"][0]["message"]["content"].strip()
            return json.loads(raw)

    async def store_thought(self, content: str, session_id: Optional[str] = None, source: str = "voice_conversation") -> None:
        """Store a thought with embedding and metadata. Run as background task — never blocks voice pipeline."""
        try:
            # Run embedding and metadata extraction in parallel — exactly as Nate's architecture specifies
            embedding, metadata = await asyncio.gather(
                self.get_embedding(content),
                self.extract_metadata(content)
            )
            
            metadata["source"] = source
            metadata["session_id"] = session_id
            metadata["captured_at"] = datetime.utcnow().isoformat()

            self.supabase.table("thoughts").insert({
                "content": content,
                "embedding": embedding,
                "metadata": metadata
            }).execute()
            
        except Exception as e:
            # Graceful degradation — memory failure never crashes voice pipeline
            print(f"[MemoryManager] Store failed (non-fatal): {e}")

    async def retrieve_relevant_thoughts(self, query: str) -> list[dict]:
        """Semantic search via match_thoughts RPC. Returns top matches by meaning."""
        try:
            query_embedding = await self.get_embedding(query)
            
            result = self.supabase.rpc("match_thoughts", {
                "query_embedding": query_embedding,
                "match_threshold": self.match_threshold,
                "match_count": self.match_count
            }).execute()
            
            return result.data or []
        except Exception as e:
            print(f"[MemoryManager] Retrieve failed (non-fatal): {e}")
            return []

    async def build_memory_context(self, query: str) -> str:
        """Build memory context block ready to prepend to system prompt."""
        if not self.enabled:
            return ""
        
        thoughts = await self.retrieve_relevant_thoughts(query)
        
        if not thoughts:
            return ""
        
        lines = ["[MEMORY CONTEXT — from previous conversations]"]
        for t in thoughts:
            lines.append(f"- {t['content']}")
        lines.append("[END MEMORY CONTEXT]")
        
        return "\n".join(lines)

    async def summarize_and_store_session(self, conversation_history: list[dict], session_id: str) -> None:
        """Extract key facts from completed conversation and store as individual thoughts."""
        try:
            history_text = "\n".join([
                f"{turn['role'].upper()}: {turn['content']}" 
                for turn in conversation_history
            ])
            
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    "https://openrouter.ai/api/v1/chat/completions",
                    headers={
                        "Authorization": f"Bearer {self.openrouter_key}",
                        "Content-Type": "application/json"
                    },
                    json={
                        "model": self.metadata_model,
                        "messages": [{
                            "role": "user",
                            "content": f"""Extract 3-7 key facts, preferences, or important information from this conversation that would be useful to remember in future conversations. Format as a simple bulleted list. Focus on: facts about the user, decisions made, preferences expressed, important context.

Conversation:
{history_text}

Return only the bullet points, nothing else:"""
                        }],
                        "temperature": 0.3
                    },
                    timeout=15.0
                )
                response.raise_for_status()
                facts_text = response.json()["choices"][0]["message"]["content"]
            
            # Store each extracted fact as an individual thought
            facts = [f.strip().lstrip("•-").strip() for f in facts_text.strip().split("\n") if f.strip()]
            
            store_tasks = [
                self.store_thought(fact, session_id=session_id, source="session_summary")
                for fact in facts if fact
            ]
            await asyncio.gather(*store_tasks)
            
        except Exception as e:
            print(f"[MemoryManager] Session summary failed (non-fatal): {e}")


STEP 6 — INTEGRATE INTO EXISTING VOICE PIPELINE
After reading the existing code in Step 1, integrate as follows. Adapt the exact hook points to match whatever framework and conversation loop structure you found:
Initialize once at startup:

from memory_manager import MemoryManager
memory_manager = MemoryManager()
session_id = str(uuid.uuid4())
conversation_history = []


At conversation start — speculative pre-fetch while STT is still processing:

# Start memory fetch as soon as partial transcript is available
# This runs in parallel with STT completion — hides latency entirely
memory_task = asyncio.create_task(
    memory_manager.build_memory_context(partial_or_final_transcript)
)


Before LLM call — inject memory into system prompt:

memory_context = await memory_task  # Already done by now if STT took >100ms
if memory_context:
    effective_system_prompt = memory_context + "\n\n" + original_system_prompt
else:
    effective_system_prompt = original_system_prompt
# Pass effective_system_prompt to Gemma 3 Flash Preview call


After each assistant response — background store, never blocks:

conversation_history.append({"role": "user", "content": user_message})
conversation_history.append({"role": "assistant", "content": assistant_response})

asyncio.create_task(
    memory_manager.store_thought(
        content=f"User: {user_message}\nAssistant: {assistant_response}",
        session_id=session_id,
        source="voice_conversation"
    )
)


At session end:

asyncio.create_task(
    memory_manager.summarize_and_store_session(conversation_history, session_id)
)


STEP 7 — ENVIRONMENT VARIABLES
Add to the existing .env file:

SUPABASE_URL=<from Step 1 reconnaissance>
SUPABASE_SERVICE_ROLE_KEY=<from Step 1 reconnaissance>
OPENROUTER_API_KEY=<from Step 1 reconnaissance or user provides>
MEMORY_MATCH_THRESHOLD=0.5
MEMORY_MATCH_COUNT=5
MEMORY_ENABLED=true


STEP 8 — DEPENDENCIES
Add to requirements.txt and install:

httpx>=0.27.0
supabase>=2.4.0


Do NOT add: openai package, langchain, mem0, sentence-transformers. All embedding and LLM calls go through OpenRouter via httpx directly.

STEP 9 — TEST BEFORE FINISHING
	1.	Run the SQL in Supabase — confirm thoughts table and match_thoughts function exist
	2.	Test storing one thought manually by calling asyncio.run(memory_manager.store_thought("Test thought about eBay listings"))
	3.	Confirm a row appears in Supabase Table Editor with a populated embedding column
	4.	Test retrieval: asyncio.run(memory_manager.retrieve_relevant_thoughts("eBay business")) — should return the test row
	5.	Start the voice agent — confirm it works exactly as before
	6.	Have a short conversation — verify rows are being written to Supabase in real time
	7.	Restart and have another conversation — confirm prior conversation memories appear in context
If anything fails, read the error, fix it, and retry at least 3 times before surfacing to the user.

CONSTRAINTS
	∙	Do not alter voice pipeline behavior in any user-noticeable way
	∙	All memory operations are either pre-fetched or background tasks — zero blocking of voice response path
	∙	Use OpenRouter for all AI calls (embeddings + metadata) — not direct OpenAI API
	∙	Use 1536-dimensional embeddings exclusively — matches Nate’s schema
	∙	Table name is thoughts, function name is match_thoughts — exact names, no substitution
	∙	Graceful degradation: catch all exceptions in memory operations, log warning, continue without memory
	∙	Agent must function normally if Supabase or OpenRouter is unreachable

That’s the corrected prompt based on Nate’s actual documented architecture. The key fixes from my earlier version: OpenRouter instead of direct APIs, 1536-dim embeddings instead of 384, thoughts table instead of memories, and metadata extraction running in parallel server-side exactly as Nate designed it.​​​​​​​​​​​​​​​​