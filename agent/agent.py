"""
Voice AI Agent — LiveKit Agents v1.x

Pipeline: Silero VAD → faster-whisper (STT) → Ollama (LLM) → Kokoro (TTS)

All three backends expose OpenAI-compatible APIs, so we use the single
`livekit-plugins-openai` plugin with custom base_url for each.

Environment variables (set via docker-compose.yml / .env):
  LIVEKIT_URL, LIVEKIT_API_KEY, LIVEKIT_API_SECRET  — agent ↔ LiveKit server
  OLLAMA_BASE_URL, OLLAMA_MODEL                      — LLM
  WHISPER_BASE_URL, WHISPER_MODEL                    — STT
  KOKORO_BASE_URL, KOKORO_MODEL, KOKORO_VOICE        — TTS
"""

import os
import logging

import httpx
from dotenv import load_dotenv
import openai as openai_pkg

from livekit import agents
from livekit.agents import AgentSession, Agent, AgentServer, room_io
from livekit.plugins import openai, silero

load_dotenv(".env.local")

logger = logging.getLogger("voice-agent")
logger.setLevel(logging.INFO)

# ─── Agent definition ────────────────────────────────────────────
class VoiceAssistant(Agent):
    """
    The persona that the LLM adopts. Keep instructions short and
    free of markdown / emojis — the TTS will read them literally.
    """

    def __init__(self) -> None:
        super().__init__(
            instructions=(
                "You are a friendly, helpful voice assistant running entirely "
                "on the user's own hardware. You are a conversational AI only. "
                "You cannot browse the internet, play music, control smart "
                "home devices, make calls, send messages, or access any "
                "external services. Never claim you can do things you cannot. "
                "Keep answers concise — one to three sentences unless asked "
                "for detail. Never use markdown, bullet points, or emojis "
                "in your responses because they will be read aloud. "
                "If you don't know something, say so honestly."
            ),
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

    # --- LLM: Ollama via OpenAI-compatible API ---
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

    # --- TTS: Kokoro via OpenAI-compatible API ---
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

    # --- VAD: Silero (runs on CPU inside this container) ---
    vad = silero.VAD.load()

    # --- Assemble the voice session ---
    session = AgentSession(
        stt=stt,
        llm=llm,
        tts=tts,
        vad=vad,
    )

    await session.start(
        room=ctx.room,
        agent=VoiceAssistant(),
    )

    logger.info("Agent session started in room %s", ctx.room.name)

    # Generate an initial greeting (fire-and-forget — don't block the entrypoint)
    session.generate_reply(
        instructions="Greet the user warmly and let them know you're ready to help."
    )


# ─── CLI entry point ─────────────────────────────────────────────
if __name__ == "__main__":
    agents.cli.run_app(server)
