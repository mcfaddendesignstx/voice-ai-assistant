"""
Voice AI Agent — LiveKit Agents v1.x

Pipeline: Silero VAD → faster-whisper (STT) → Gemini/Ollama (LLM) → ElevenLabs/Kokoro (TTS)
Memory:   Supabase pgvector + OpenRouter (text-embedding-3-small, 1536-dim)

STT backend exposes an OpenAI-compatible API via `livekit-plugins-openai`.
LLM uses Gemini (cloud) when GEMINI_API_KEY is set, otherwise falls back
to Ollama (local). TTS uses ElevenLabs (cloud) when ELEVENLABS_API_KEY is
set, otherwise falls back to Kokoro (local).
Persistent memory (Supabase pgvector) is injected into the system prompt
when MEMORY_ENABLED=true and SUPABASE_URL/SUPABASE_ANON_KEY are set.

Environment variables (set via docker-compose.yml / .env):
  LIVEKIT_URL, LIVEKIT_API_KEY, LIVEKIT_API_SECRET  — agent ↔ LiveKit server
  GEMINI_API_KEY, GEMINI_MODEL                       — LLM (cloud, optional)
  OLLAMA_BASE_URL, OLLAMA_MODEL                      — LLM (local fallback)
  WHISPER_BASE_URL, WHISPER_MODEL                    — STT
  KOKORO_BASE_URL, KOKORO_MODEL, KOKORO_VOICE        — TTS (local fallback)
  ELEVENLABS_API_KEY, ELEVENLABS_VOICE_ID             — TTS (cloud, optional)
  SUPABASE_URL, SUPABASE_SERVICE_ROLE_KEY/ANON_KEY    — persistent memory
  OPENROUTER_API_KEY                                  — embeddings + metadata
  MEMORY_ENABLED, MEMORY_MATCH_THRESHOLD, MEMORY_MATCH_COUNT
"""

import os
import logging
import asyncio
import uuid
from datetime import datetime, timezone

import httpx
from dotenv import load_dotenv
import openai as openai_pkg

from livekit import agents
from livekit.agents import AgentSession, Agent, AgentServer, room_io, llm as llm_module
from livekit.plugins import openai, silero, elevenlabs, google

from memory_manager import MemoryManager

load_dotenv(".env.local")

logger = logging.getLogger("voice-agent")
logger.setLevel(logging.INFO)

# ─── Base system prompt (memory context prepended at runtime) ─────
_BASE_INSTRUCTIONS = (
    "You are a friendly, helpful voice assistant with persistent memory. "
    "You remember previous conversations with the user. "
    "When a MEMORY CONTEXT block appears in your context, it contains real facts "
    "from past conversations — treat them as things you genuinely remember and "
    "reference them naturally when relevant. "
    "If the user asks what you last talked about or what you remember, "
    "tell them based on the memory context you have been given. "
    "You are a conversational AI only. "
    "You cannot browse the internet, play music, control smart "
    "home devices, make calls, send messages, or access any "
    "external services. Never claim you can do things you cannot. "
    "Keep answers concise — one to three sentences unless asked "
    "for detail. Never use markdown, bullet points, or emojis "
    "in your responses because they will be read aloud. "
    "If you don't know something, say so honestly."
)


# ─── Agent definition ────────────────────────────────────────────
class VoiceAssistant(Agent):
    """
    The persona that the LLM adopts. Keep instructions short and
    free of markdown / emojis — the TTS will read them literally.
    Memory context is injected before each LLM call via on_user_turn_completed.
    """

    def __init__(self, memory: MemoryManager, session_id: str) -> None:
        now = datetime.now(timezone.utc).astimezone()
        instructions = (
            f"Current date and time: {now.strftime('%A, %B %d, %Y at %I:%M %p %Z')}.\n\n"
            + _BASE_INSTRUCTIONS
        )
        super().__init__(instructions=instructions)
        self._memory = memory
        self._session_id = session_id
        self._conversation_history: list[str] = []

    async def on_user_turn_completed(
        self, turn_ctx: llm_module.ChatContext, new_message: llm_module.ChatMessage
    ) -> None:
        """Called after the user finishes speaking, before the LLM responds.
        Retrieve relevant memories and inject them into the chat context."""
        user_text = new_message.text_content or ""
        if not user_text:
            return

        # Retrieve memories (targets < 100 ms)
        memory_context = await self._memory.build_memory_context(user_text, current_session_id=self._session_id)
        if memory_context:
            turn_ctx.add_message(role="system", content=memory_context)
            logger.info("Injected memory context (%d chars)", len(memory_context))

        # Track conversation for end-of-session summary
        self._conversation_history.append(f"User: {user_text}")

    async def on_exit(self) -> None:
        """Called when the agent session ends — summarize and persist."""
        if self._conversation_history:
            history_text = "\n".join(self._conversation_history)
            asyncio.create_task(
                self._memory.summarize_and_store_session(
                    conversation_history=history_text,
                    session_id=self._session_id,
                )
            )


# ─── Agent server & session wiring ──────────────────────────────
server = AgentServer()


@server.rtc_session(agent_name="voice-assistant")
async def entrypoint(ctx: agents.JobContext):
    """Called once per LiveKit room that requests an agent."""

    # Long timeout for first-request model loading (whisper, ollama, kokoro)
    _timeout = httpx.Timeout(timeout=120.0, connect=30.0)

    # --- STT: faster-whisper via OpenAI-compatible API ---
    stt_client = openai_pkg.AsyncClient(
        base_url=os.getenv("WHISPER_BASE_URL", "http://whisper:8000/v1"),
        api_key="not-needed",
        timeout=_timeout,
    )
    stt = openai.STT(
        model=os.getenv("WHISPER_MODEL", "Systran/faster-whisper-large-v3"),
        base_url=os.getenv("WHISPER_BASE_URL", "http://whisper:8000/v1"),
        api_key="not-needed",
        client=stt_client,
    )

    # --- LLM: route by model selector (gemini-flash | claude-haiku | gpt-4o-mini) ---
    model_choice = (getattr(ctx.job, "metadata", None) or "").strip() or "gemini-flash"
    logger.info("Model selected: %s", model_choice)

    gemini_key = os.getenv("GEMINI_API_KEY", "")
    openrouter_key = os.getenv("OPENROUTER_API_KEY", "")

    if model_choice == "claude-haiku" and openrouter_key:
        llm_client = openai_pkg.AsyncClient(
            base_url="https://openrouter.ai/api/v1",
            api_key=openrouter_key,
        )
        llm = openai.LLM(model="anthropic/claude-haiku-4-5", client=llm_client)
        logger.info("Using Claude Haiku 4.5 via OpenRouter")
    elif model_choice == "gpt-4o-mini" and openrouter_key:
        llm_client = openai_pkg.AsyncClient(
            base_url="https://openrouter.ai/api/v1",
            api_key=openrouter_key,
        )
        llm = openai.LLM(model="openai/gpt-4.1-mini", client=llm_client)
        logger.info("Using GPT-4.1-mini via OpenRouter")
    elif gemini_key:
        llm = google.LLM(
            model=os.getenv("GEMINI_MODEL", "gemini-2.0-flash-exp"),
            api_key=gemini_key,
        )
        logger.info("Using Gemini Flash (cloud)")
    else:
        llm_client = openai_pkg.AsyncClient(
            base_url=os.getenv("OLLAMA_BASE_URL", "http://ollama:11434/v1"),
            api_key="ollama",
            timeout=_timeout,
        )
        llm = openai.LLM.with_ollama(
            model=os.getenv("OLLAMA_MODEL", "llama3.1:8b"),
            base_url=os.getenv("OLLAMA_BASE_URL", "http://ollama:11434/v1"),
            client=llm_client,
        )
        logger.info("Using Ollama LLM (local)")

    # --- TTS: ElevenLabs (cloud) or Kokoro (local fallback) ---
    elevenlabs_key = os.getenv("ELEVENLABS_API_KEY", "")
    if elevenlabs_key:
        tts = elevenlabs.TTS(
            voice_id=os.getenv("ELEVENLABS_VOICE_ID", "cjVigY5qzO86Huf0OWal"),
            model="eleven_flash_v2_5",
            api_key=elevenlabs_key,
            auto_mode=True,
            language="en",
        )
        logger.info("Using ElevenLabs TTS (cloud)")
    else:
        tts_client = openai_pkg.AsyncClient(
            base_url=os.getenv("KOKORO_BASE_URL", "http://kokoro:8880/v1"),
            api_key="not-needed",
            timeout=_timeout,
        )
        tts = openai.TTS(
            model=os.getenv("KOKORO_MODEL", "kokoro"),
            voice=os.getenv("KOKORO_VOICE", "af_heart"),
            base_url=os.getenv("KOKORO_BASE_URL", "http://kokoro:8880/v1"),
            api_key="not-needed",
            client=tts_client,
        )
        logger.info("Using Kokoro TTS (local)")

    # --- VAD: Silero (runs on CPU inside this container) ---
    vad = silero.VAD.load()

    # --- Persistent memory (Supabase pgvector) ---
    memory = MemoryManager()
    session_id = str(uuid.uuid4())
    logger.info("Memory enabled: %s  session_id: %s", memory.enabled, session_id[:8])

    # --- Assemble the voice session ---
    session = AgentSession(
        stt=stt,
        llm=llm,
        tts=tts,
        vad=vad,
    )

    voice_agent = VoiceAssistant(memory=memory, session_id=session_id)

    # Hook: after each agent reply, store the exchange in background
    @session.on("agent_speech_committed")
    def _on_agent_speech(msg: llm_module.ChatMessage) -> None:
        assistant_text = msg.text_content or ""
        if not assistant_text:
            return
        voice_agent._conversation_history.append(f"Assistant: {assistant_text}")
        last_user = ""
        for line in reversed(voice_agent._conversation_history):
            if line.startswith("User:"):
                last_user = line
                break
        content = f"{last_user}\nAssistant: {assistant_text}" if last_user else f"Assistant: {assistant_text}"
        logger.info("Storing turn to memory (session %s)", session_id[:8])
        asyncio.create_task(
            memory.store_thought(
                content=content,
                session_id=session_id,
                source="voice_conversation",
            )
        )

    await session.start(
        room=ctx.room,
        agent=voice_agent,
    )

    logger.info("Agent session started in room %s", ctx.room.name)

    # Generate an initial greeting (fire-and-forget — don't block the entrypoint)
    session.generate_reply(
        instructions="Greet the user warmly and let them know you're ready to help."
    )


# ─── CLI entry point ─────────────────────────────────────────────
if __name__ == "__main__":
    agents.cli.run_app(server)
