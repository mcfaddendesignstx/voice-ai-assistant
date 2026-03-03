# Phase-by-Phase Implementation & Testing Checklist

Each phase ends with a **testable milestone**. Do not proceed to the next phase
until the current one passes all its checks.

---

## Phase 1: Docker Infrastructure (No AI yet)

**Goal:** LiveKit server + token server running, iPhone can connect and see an empty room.

### Steps
1. Copy `.env.example` to `.env` and edit `LIVEKIT_EXTERNAL_URL` to your PC's LAN IP
2. Ensure Docker Desktop is running with **WSL 2 backend** and **NVIDIA GPU support** enabled
3. Start the minimal stack:
   ```powershell
   docker compose up livekit-server token-server -d
   ```
4. Verify LiveKit is running:
   ```powershell
   curl http://localhost:7880
   ```
   Expected: returns an HTML page or 200 OK

5. Verify token server:
   ```powershell
   curl "http://localhost:8081/token?room=test&identity=user1"
   ```
   Expected: JSON with `token` and `url` fields

### Tests
- [ ] `docker compose ps` shows `livekit-server` and `token-server` healthy
- [ ] Token server returns valid JSON at `/token`
- [ ] Token server `/health` returns `{"status": "ok"}`

---

## Phase 2: GPU Services (Ollama + Whisper + Kokoro)

**Goal:** All GPU containers start and their APIs respond.

### Steps
1. Start GPU services:
   ```powershell
   docker compose up ollama whisper kokoro -d
   ```
2. Pull the LLM model into Ollama (first time only, ~4.7 GB):
   ```powershell
   docker compose exec ollama ollama pull llama3.1:8b
   ```
3. Test Ollama:
   ```powershell
   curl http://localhost:11434/api/generate -d '{"model":"llama3.1:8b","prompt":"Say hello","stream":false}'
   ```
4. Test faster-whisper (may take 60s+ for first model load):
   ```powershell
   # Check health
   curl http://localhost:8000/health
   ```
5. Test Kokoro TTS:
   ```powershell
   curl http://localhost:8880/health
   ```

### Tests
- [ ] `docker compose ps` shows ollama, whisper, kokoro all running
- [ ] `nvidia-smi` inside any GPU container shows the RTX 5090
- [ ] Ollama generates text (curl test above)
- [ ] Whisper health endpoint responds
- [ ] Kokoro health endpoint responds
- [ ] `docker stats` shows reasonable GPU memory usage (<24 GB total)

### RTX 5090 Troubleshooting
- If containers crash with CUDA errors, check: `nvidia-smi` on the host
- Ensure NVIDIA driver is 570+ (`nvidia-smi` shows driver version)
- If faster-whisper fails, try changing `WHISPER__COMPUTE_TYPE` to `int8` in docker-compose.yml
- If Kokoro fails, check logs: `docker compose logs kokoro`

---

## Phase 3: LiveKit Agent (Voice Pipeline)

**Goal:** Agent connects to LiveKit and is ready to join rooms.

### Steps
1. Start the agent:
   ```powershell
   docker compose up agent -d
   ```
2. Check agent logs:
   ```powershell
   docker compose logs -f agent
   ```
   Expected: "Worker registered" or similar connection message

3. Test with LiveKit's web playground:
   - Open `https://agents-playground.livekit.io`
   - Enter your LiveKit URL: `ws://<your-pc-ip>:7880`
   - Enter API Key: `devkey`
   - Enter API Secret: `secret_change_me_in_production`
   - Connect — the agent should join and greet you

### Tests
- [ ] Agent container stays running (no crash loop)
- [ ] Agent logs show successful connection to LiveKit
- [ ] LiveKit playground: agent joins and sends a greeting
- [ ] LiveKit playground: speak into mic → agent responds with voice
- [ ] Latency is under ~2 seconds end-to-end (STT + LLM + TTS)

### Troubleshooting
- Agent crash with "connection refused": ensure `LIVEKIT_URL=ws://livekit-server:7880`
- STT errors: check `docker compose logs whisper`
- LLM errors: ensure you pulled the Ollama model in Phase 2
- TTS errors: check `docker compose logs kokoro`
- Slow responses: try a smaller Ollama model (`llama3.2:3b`)

---

## Phase 4: iOS App (Voice Chat)

**Goal:** iPhone connects to LiveKit, voice chat works end-to-end.

### Steps
1. Follow `ios/SETUP.md` to create the Xcode project on your Mac
2. Set the token server URL in `Config.swift` to your PC's IP
3. Build and run on your iPhone
4. Tap Connect — you should hear the agent greet you
5. Speak — the agent should respond

### Tests
- [ ] App builds and installs on iPhone without errors
- [ ] Connect button reaches the token server and gets a JWT
- [ ] LiveKit connection established (status shows "Connected")
- [ ] Agent joins the room (status shows "Agent connected")
- [ ] You hear the agent's greeting
- [ ] You speak → agent responds with voice
- [ ] Transcriptions appear in the Chat tab
- [ ] You can type a message in the Chat tab → agent responds
- [ ] Mute button works (agent stops hearing you)
- [ ] Disconnect button works

### Troubleshooting
- "Could not connect": check firewall — ports 7880, 7881, 8081, 50000-50020/UDP
- No audio: check iPhone volume, check Kokoro logs
- Microphone not working: check iOS permission in Settings → VoiceAssistant

---

## Phase 5: Tailscale Remote Access

**Goal:** Use the app from anywhere, not just local Wi-Fi.

### Steps
1. Follow `TAILSCALE.md` for full setup
2. Install Tailscale on Windows PC and iPhone
3. Update `.env` → `LIVEKIT_EXTERNAL_URL=ws://<tailscale-ip>:7880`
4. Update the app's Settings → Token Server URL to `http://<tailscale-ip>:8081`
5. Restart the token-server: `docker compose restart token-server`
6. Connect from the iPhone over cellular (Wi-Fi off)

### Tests
- [ ] Tailscale shows both devices online
- [ ] `ping <tailscale-ip>` works from iPhone (via Tailscale)
- [ ] App connects and voice chat works over Tailscale
- [ ] Latency is acceptable (depends on your internet upload speed)

---

## Phase 6: Enhancements (Future)

**Goal:** Add features on top of the working voice chat.

### Ideas (in priority order)
1. **Swap LLM to cloud API** — Change `OLLAMA_BASE_URL` to an OpenAI/Anthropic endpoint
2. **MCP server for tools** — Add image generation, web search via MCP protocol
3. **Conversation history** — Persist chat to SQLite or file
4. **Multiple voices** — Let user pick Kokoro voice in Settings
5. **Wake word detection** — "Hey Assistant" activation
6. **Push notifications** — Alert when agent finishes a long task
7. **SSL/TLS** — Add HTTPS via reverse proxy (Caddy/Traefik) for production use

---

## Quick Reference: Full Stack Startup

```powershell
# Start everything
docker compose up -d

# Pull Ollama model (first time only)
docker compose exec ollama ollama pull llama3.1:8b

# Watch all logs
docker compose logs -f

# Stop everything
docker compose down

# Nuclear reset (removes volumes too)
docker compose down -v
```
