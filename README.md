# Voice AI Assistant — Self-Hosted, Persistent Memory

> *Built entirely through AI-assisted pair programming by someone with no coding background.*

A private voice AI assistant that runs on your home PC, remembers everything across sessions, and lets you talk to Claude, GPT, or Gemini — without giving your conversations to anyone.

This is a ChatGPT Voice Mode alternative you actually own. Your speech is transcribed locally on your GPU. Your memories are stored in your own database. You choose which AI model responds. Nothing is logged by a third party.

```
┌─────────────────┐     WebRTC      ┌──────────────────┐
│   iPhone App    │◄───────────────►│  LiveKit Server   │
│  (Swift/SwiftUI)│                 │  (Docker :7880)   │
└────────┬────────┘                 └────────┬──────────┘
         │ HTTP (token)                      │ Internal
         ▼                                   ▼
┌─────────────────┐              ┌──────────────────────┐
│  Token Server   │              │   LiveKit Agent      │
│  (FastAPI :8081)│              │   (Python)           │
└─────────────────┘              └──┬───────┬───────┬───┘
                                    │       │       │
                              ┌─────▼─┐ ┌──▼───┐ ┌─▼────────┐
                              │Ollama │ │Whisper│ │Kokoro TTS│
                              │:11434 │ │:8000  │ │:8880     │
                              │ (GPU) │ │ (GPU) │ │  (GPU)   │
                              └───────┘ └──────┘ └──────────┘
```

## What It Does

- **Talks back in real time** — sub-second voice response using local GPU speech synthesis
- **Remembers everything** — every session is stored as semantic vector embeddings in Supabase. Ask it what you talked about last week and it knows.
- **Model selector** — switch between Gemini 2.0 Flash, Claude Haiku 4.5, or GPT-4.1 Mini per session
- **100% local speech pipeline** — Whisper STT and Kokoro TTS run on your GPU, never leave your machine
- **Browser + iOS client** — connect from `web-test/index.html` in any browser, or build the SwiftUI app

## How the Memory Works

Every conversation is stored in a Supabase PostgreSQL database with the `pgvector` extension. When you speak, your query is embedded into 1,536-dimensional vector space and compared against everything stored. The closest semantic matches are injected into the AI's context before it responds — so it can recall facts from months ago as naturally as facts from five minutes ago.

This is the same architecture used by production AI memory products, running entirely on infrastructure you control.

## Tech Stack

| Component | Technology | Role |
|-----------|-----------|------|
| **Media Server** | [LiveKit](https://livekit.io/) (Docker) | WebRTC real-time voice streaming |
| **Voice Agent** | [LiveKit Agents](https://docs.livekit.io/agents/) (Python) | STT → LLM → TTS pipeline |
| **LLM** | Gemini / Claude / GPT via [OpenRouter](https://openrouter.ai/) | Selectable per session |
| **STT** | [faster-whisper](https://github.com/SYSTRAN/faster-whisper) (GPU) | Local speech-to-text |
| **TTS** | [Kokoro](https://github.com/remsky/Kokoro-FastAPI) (GPU) / ElevenLabs | Local or cloud voice synthesis |
| **Memory** | [Supabase](https://supabase.com/) + pgvector | Persistent semantic memory store |
| **Embeddings** | OpenRouter `text-embedding-3-small` | 1,536-dim vectors for memory retrieval |
| **Token Server** | FastAPI (Python) | Mints LiveKit JWTs, passes model choice to agent |
| **Web Client** | Vanilla HTML/JS + LiveKit SDK | Browser-based voice interface |
| **iOS App** | SwiftUI + LiveKit Swift SDK | Native iPhone client (requires Mac to build) |

## Hardware Requirements

| Component | Minimum | Recommended |
|-----------|---------|-------------|
| **GPU** | NVIDIA RTX 3060 (12 GB VRAM) | RTX 4090 / RTX 5090 |
| **RAM** | 16 GB | 32 GB+ |
| **OS** | Windows 10/11 with Docker Desktop | Windows 11 + WSL 2 |
| **NVIDIA Driver** | 535+ (RTX 30/40 series) | 570+ (RTX 5090 Blackwell) |
| **iPhone** | iOS 17.0+ | iOS 17.0+ |

## Quick Start

### 1. Clone and Configure

```powershell
git clone <your-repo-url> voice-assistant
cd voice-assistant
copy .env.example .env
```

Edit `.env`:
- Set `LIVEKIT_EXTERNAL_URL` to `ws://<your-pc-ip>:7880`
- Optionally change `LIVEKIT_API_SECRET` for security

### 2. Start Backend Services

```powershell
# Start everything
docker compose up -d

# Pull the LLM model (first time only, ~4.7 GB download)
docker compose exec ollama ollama pull llama3.1:8b

# Watch logs
docker compose logs -f
```

### 3. Verify Services

```powershell
# LiveKit server
curl http://localhost:7880

# Token server
curl "http://localhost:8081/token?room=test&identity=user1"

# Ollama
curl http://localhost:11434/api/tags
```

### 4. Build the iOS App

See [ios/SETUP.md](ios/SETUP.md) for step-by-step Xcode project creation.

### 5. Connect and Talk

1. Open the app on your iPhone
2. Verify the token server URL in Settings
3. Tap **Connect**
4. Start talking!

## Project Structure

```
.
├── docker-compose.yml          # All backend services
├── livekit.yaml                # LiveKit server configuration
├── .env.example                # Environment variables template
├── agent/
│   ├── Dockerfile
│   ├── requirements.txt
│   └── agent.py                # LiveKit Agent (STT → LLM → TTS)
├── token-server/
│   ├── Dockerfile
│   ├── requirements.txt
│   └── server.py               # JWT minting for iOS app
├── ios/
│   ├── SETUP.md                # Xcode project setup guide
│   └── VoiceAssistant/
│       ├── VoiceAssistantApp.swift
│       ├── Config.swift
│       ├── Info.plist
│       ├── Models/
│       │   └── ChatMessage.swift
│       ├── Services/
│       │   └── TokenService.swift
│       ├── ViewModels/
│       │   ├── RoomManager.swift
│       │   └── ChatViewModel.swift
│       └── Views/
│           ├── ContentView.swift
│           ├── ConnectView.swift
│           ├── VoiceSessionView.swift
│           ├── ChatView.swift
│           └── SettingsView.swift
├── PHASES.md                   # Phase-by-phase testing checklist
├── TAILSCALE.md                # Remote access setup guide
└── README.md                   # This file
```

## Implementation Phases

Follow [PHASES.md](PHASES.md) for detailed step-by-step instructions:

| Phase | Milestone | What You Test |
|-------|-----------|---------------|
| **1** | Docker Infrastructure | LiveKit + token server running, HTTP responses OK |
| **2** | GPU Services | Ollama, Whisper, Kokoro all start with GPU acceleration |
| **3** | Voice Agent | Agent joins rooms, voice pipeline works in LiveKit playground |
| **4** | iOS App | iPhone connects, bidirectional voice chat works |
| **5** | Tailscale | Remote access works over VPN from anywhere |
| **6** | Enhancements | Swap LLMs, add MCP tools, conversation history |

## Swapping the LLM Backend

The agent uses OpenAI-compatible APIs for all three AI services. To swap
the LLM to a cloud provider:

```env
# .env — switch from Ollama to OpenAI
OLLAMA_BASE_URL=https://api.openai.com/v1
OLLAMA_MODEL=gpt-4o-mini
```

You'll also need to set `OPENAI_API_KEY` in the agent's environment. The
same pattern works for Anthropic, Groq, Together, or any OpenAI-compatible
API.

## MCP Server Support (Future)

The LiveKit Agents framework supports [tool use](https://docs.livekit.io/agents/build/tools/).
You can add MCP-compatible tools to the agent for:
- **Image generation** (DALL-E, Stable Diffusion)
- **Web search** (Brave, Tavily)
- **Smart home control** (Home Assistant)
- **Calendar/email** (via MCP protocol)

See Phase 6 in [PHASES.md](PHASES.md) for details.

## Remote Access

See [TAILSCALE.md](TAILSCALE.md) for Tailscale VPN setup instructions.

## Ports Reference

| Port | Protocol | Service | Exposed To |
|------|----------|---------|------------|
| 7880 | TCP | LiveKit HTTP/WS | LAN / Tailscale |
| 7881 | TCP | LiveKit ICE (TCP fallback) | LAN / Tailscale |
| 50000-50020 | UDP | WebRTC media | LAN / Tailscale |
| 8081 | TCP | Token Server | LAN / Tailscale |
| 11434 | TCP | Ollama API | localhost (debug) |
| 8000 | TCP | Whisper API | internal only |
| 8880 | TCP | Kokoro TTS API | internal only |

## License

This project scaffold is provided as-is for personal use. The iOS app is
proprietary (not open source) — you own and control the code. Backend
services use their respective open-source licenses.
