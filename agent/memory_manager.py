"""
Persistent Vector Memory — Nate B. Jones "Open Brain" architecture.

Uses Supabase pgvector for storage, OpenRouter for embeddings
(text-embedding-3-small, 1536-dim) and metadata extraction (gpt-4o-mini).
Embedding + metadata run in parallel per Nate's spec.

Table: thoughts   Function: match_thoughts

All operations are async and non-blocking to the voice pipeline.
Graceful degradation: any failure logs a warning and continues.

Requires:
  SUPABASE_URL                  — Supabase project URL
  SUPABASE_SERVICE_ROLE_KEY     — bypasses RLS (preferred)
  SUPABASE_ANON_KEY             — fallback if service role unavailable
  OPENROUTER_API_KEY            — embeddings + metadata extraction
  MEMORY_ENABLED=true           — kill switch
  MEMORY_MATCH_THRESHOLD=0.5    — cosine similarity floor
  MEMORY_MATCH_COUNT=5          — max thoughts to retrieve
"""

import os
import json
import logging
import asyncio
from datetime import datetime, timezone
from typing import Optional

import httpx
from supabase import create_client, Client

logger = logging.getLogger("voice-agent.memory")
logger.setLevel(logging.INFO)


class MemoryManager:
    """
    Persistent memory layer backed by Supabase pgvector + OpenRouter.

    All public methods are async.  Store/summarize operations are designed
    to be fired as background tasks so they never block the voice pipeline.
    """

    def __init__(self) -> None:
        self.enabled = os.getenv("MEMORY_ENABLED", "true").lower() == "true"
        self.match_threshold = float(os.getenv("MEMORY_MATCH_THRESHOLD", "0.5"))
        self.match_count = int(os.getenv("MEMORY_MATCH_COUNT", "5"))
        self._supabase: Optional[Client] = None
        self._openrouter_key: str = ""
        self._embedding_model = "openai/text-embedding-3-small"
        self._metadata_model = "openai/gpt-4o-mini"

        if not self.enabled:
            return

        # Supabase client (prefer service_role key, fall back to anon)
        url = os.getenv("SUPABASE_URL", "")
        key = os.getenv("SUPABASE_SERVICE_ROLE_KEY", "") or os.getenv("SUPABASE_ANON_KEY", "")
        self._openrouter_key = os.getenv("OPENROUTER_API_KEY", "")

        if not url or not key:
            logger.warning("SUPABASE_URL or key not set — memory disabled")
            self.enabled = False
            return
        if not self._openrouter_key:
            logger.warning("OPENROUTER_API_KEY not set — memory disabled")
            self.enabled = False
            return

        try:
            self._supabase = create_client(url, key)
            logger.info("MemoryManager connected to Supabase (Open Brain)")
        except Exception as e:
            logger.warning("MemoryManager Supabase init failed: %s", e)
            self.enabled = False

    # ── OpenRouter helpers ─────────────────────────────────────────

    async def get_embedding(self, text: str) -> list[float]:
        """Generate 1536-dim embedding via OpenRouter → text-embedding-3-small."""
        async with httpx.AsyncClient() as client:
            resp = await client.post(
                "https://openrouter.ai/api/v1/embeddings",
                headers={
                    "Authorization": f"Bearer {self._openrouter_key}",
                    "Content-Type": "application/json",
                },
                json={"model": self._embedding_model, "input": text},
                timeout=10.0,
            )
            resp.raise_for_status()
            return resp.json()["data"][0]["embedding"]

    async def extract_metadata(self, content: str) -> dict:
        """Extract structured metadata via OpenRouter → gpt-4o-mini.
        Runs in parallel with embedding per Nate's architecture."""
        try:
            async with httpx.AsyncClient() as client:
                resp = await client.post(
                    "https://openrouter.ai/api/v1/chat/completions",
                    headers={
                        "Authorization": f"Bearer {self._openrouter_key}",
                        "Content-Type": "application/json",
                    },
                    json={
                        "model": self._metadata_model,
                        "messages": [
                            {
                                "role": "user",
                                "content": (
                                    "Extract metadata from this thought. Return ONLY valid JSON with these fields:\n"
                                    "- type: one of [person_note, decision, insight, meeting_debrief, ai_save, general]\n"
                                    "- topics: array of topic strings\n"
                                    "- people: array of person names mentioned\n"
                                    "- action_items: array of action items if any\n\n"
                                    f"Thought: {content}\n\nJSON only, no explanation:"
                                ),
                            }
                        ],
                        "temperature": 0.1,
                    },
                    timeout=10.0,
                )
                resp.raise_for_status()
                raw = resp.json()["choices"][0]["message"]["content"].strip()
                # Strip markdown fences if present
                if raw.startswith("```"):
                    raw = raw.split("\n", 1)[1].rsplit("```", 1)[0].strip()
                return json.loads(raw)
        except Exception as e:
            logger.debug("Metadata extraction failed (non-fatal): %s", e)
            return {"type": "general", "topics": [], "people": [], "action_items": []}

    # ── Storage ────────────────────────────────────────────────────

    async def store_thought(
        self,
        content: str,
        session_id: Optional[str] = None,
        source: str = "voice_conversation",
    ) -> None:
        """Store a thought with embedding + metadata (in parallel).
        Designed as a background task — never blocks the voice pipeline."""
        if not self.enabled or not self._supabase:
            return

        try:
            # Parallel: embedding + metadata extraction (Nate's architecture)
            embedding, metadata = await asyncio.gather(
                self.get_embedding(content),
                self.extract_metadata(content),
            )
            metadata["source"] = source
            metadata["session_id"] = session_id
            metadata["captured_at"] = datetime.now(timezone.utc).isoformat()

            await asyncio.to_thread(
                lambda: self._supabase.table("thoughts")
                .insert({"content": content, "embedding": embedding, "metadata": metadata})
                .execute()
            )
            logger.debug("Stored thought: %s", content[:80])
        except Exception as e:
            logger.warning("Thought storage failed (non-fatal): %s", e)

    # ── Retrieval ──────────────────────────────────────────────────

    async def retrieve_relevant_thoughts(self, query: str) -> list[dict]:
        """Semantic search via match_thoughts RPC."""
        if not self.enabled or not self._supabase:
            return []

        try:
            query_embedding = await self.get_embedding(query)
            result = await asyncio.to_thread(
                lambda: self._supabase.rpc(
                    "match_thoughts",
                    {
                        "query_embedding": query_embedding,
                        "match_threshold": self.match_threshold,
                        "match_count": self.match_count,
                    },
                ).execute()
            )
            return result.data or []
        except Exception as e:
            logger.warning("Thought retrieval failed (non-fatal): %s", e)
            return []

    async def retrieve_recent_thoughts(self, limit: int = 3) -> list[dict]:
        """Fetch the most recent thoughts by created_at — regardless of semantic match."""
        if not self.enabled or not self._supabase:
            return []
        try:
            result = await asyncio.to_thread(
                lambda: self._supabase.table("thoughts")
                .select("id, content, metadata, created_at")
                .order("created_at", desc=True)
                .limit(limit)
                .execute()
            )
            return result.data or []
        except Exception as e:
            logger.warning("Recent thoughts fetch failed (non-fatal): %s", e)
            return []

    async def build_memory_context(self, query: str) -> str:
        """Build memory context block to prepend to system prompt.
        Combines semantic search results with most recent thoughts."""
        if not self.enabled:
            return ""

        # Run semantic search + recency fetch in parallel
        semantic, recent = await asyncio.gather(
            self.retrieve_relevant_thoughts(query),
            self.retrieve_recent_thoughts(limit=3),
        )

        # Merge, deduplicate by id, semantic results first
        seen = set()
        merged = []
        for t in semantic + recent:
            if t["id"] not in seen:
                seen.add(t["id"])
                merged.append(t)

        if not merged:
            return ""

        lines = ["[MEMORY CONTEXT — from previous conversations]"]
        for t in merged:
            lines.append(f"- {t['content']}")
        lines.append("[END MEMORY CONTEXT]")
        return "\n".join(lines)

    # ── Session summarization ──────────────────────────────────────

    async def summarize_and_store_session(
        self,
        conversation_history: str,
        session_id: str,
    ) -> None:
        """Extract key facts via gpt-4o-mini, store each as an individual thought."""
        if not self.enabled:
            return

        try:
            async with httpx.AsyncClient() as client:
                resp = await client.post(
                    "https://openrouter.ai/api/v1/chat/completions",
                    headers={
                        "Authorization": f"Bearer {self._openrouter_key}",
                        "Content-Type": "application/json",
                    },
                    json={
                        "model": self._metadata_model,
                        "messages": [
                            {
                                "role": "user",
                                "content": (
                                    "Extract 3-7 key facts, preferences, or important information "
                                    "from this conversation that would be useful to remember in "
                                    "future conversations. Format as a simple bulleted list. "
                                    "Focus on: facts about the user, decisions made, preferences "
                                    "expressed, important context.\n\n"
                                    f"Conversation:\n{conversation_history}\n\n"
                                    "Return only the bullet points, nothing else:"
                                ),
                            }
                        ],
                        "temperature": 0.3,
                    },
                    timeout=15.0,
                )
                resp.raise_for_status()
                facts_text = resp.json()["choices"][0]["message"]["content"]

            facts = [
                f.strip().lstrip("•-–* ").strip()
                for f in facts_text.strip().splitlines()
                if f.strip()
            ]

            # Also store a single narrative topic entry so "what did we last talk about?" works
            topic_task = self._store_topic_summary(conversation_history, session_id)

            tasks = [
                self.store_thought(fact, session_id=session_id, source="session_summary")
                for fact in facts
                if len(fact) > 10
            ]
            if tasks:
                await asyncio.gather(*tasks, topic_task)
                logger.info("Stored %d facts + topic from session %s", len(tasks), session_id[:8])
        except Exception as e:
            logger.warning("Session summarization failed (non-fatal): %s", e)

    async def _store_topic_summary(self, conversation_history: str, session_id: str) -> None:
        """Store a single narrative sentence describing what the session was about."""
        try:
            async with httpx.AsyncClient() as client:
                resp = await client.post(
                    "https://openrouter.ai/api/v1/chat/completions",
                    headers={
                        "Authorization": f"Bearer {self._openrouter_key}",
                        "Content-Type": "application/json",
                    },
                    json={
                        "model": self._metadata_model,
                        "messages": [
                            {
                                "role": "user",
                                "content": (
                                    "Summarize this conversation in ONE sentence starting with "
                                    "'In our last conversation, we discussed...' "
                                    "Be specific about the topics covered.\n\n"
                                    f"Conversation:\n{conversation_history}\n\n"
                                    "One sentence only:"
                                ),
                            }
                        ],
                        "temperature": 0.3,
                    },
                    timeout=15.0,
                )
                resp.raise_for_status()
                topic = resp.json()["choices"][0]["message"]["content"].strip()
            await self.store_thought(topic, session_id=session_id, source="session_topic")
        except Exception as e:
            logger.debug("Topic summary failed (non-fatal): %s", e)
