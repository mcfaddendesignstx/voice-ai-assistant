# Substack Post Outline: I Built a Voice AI That Remembers Everything — Without Writing a Single Line of Code

---

## Hook (first 2-3 sentences)
I'm not a developer. I've never written a line of Python in my life. But I now run a private voice AI assistant on my home PC that knows who I am, remembers our conversations across sessions, and responds in real time — and I built every part of it myself using AI.

---

## Section 1: The Problem With ChatGPT Voice Mode
- It forgets everything the moment you close the app
- Every conversation goes to OpenAI's servers — you own nothing
- You're training their model with your personal life
- You pay a subscription for a product you don't control

**The question I kept asking:** What if I could have something like this that was actually mine?

---

## Section 2: What I Built
A self-hosted voice AI assistant running entirely on my home PC with:
- **Real-time voice** — I talk, it listens, it responds. No typing.
- **Persistent memory** — It remembers my name, my job, my family, what we talked about last week. Across sessions. Permanently.
- **Multiple AI brains** — I can switch between Google Gemini, Claude, or GPT models on the fly depending on what I need
- **My hardware, my data** — Speech processing runs locally on my GPU. Nothing leaves my house except the AI inference calls.

---

## Section 3: How I Actually Built It (The Honest Part)
I used Windsurf (an AI coding IDE) and worked with Cascade (the AI assistant inside it) as a pair programmer. I described what I wanted. It wrote the code. I tested it. We debugged together. I made decisions — it built.

This took weeks of iteration. It wasn't magic. But I never had to understand the code to direct it.

**What this says about where we are:** The barrier to building real software is no longer knowing how to code. It's knowing what you want and being able to communicate it clearly.

---

## Section 4: The Tech (Briefly — Link to GitHub)
For those who want to know:
- **LiveKit** — handles real-time WebRTC voice streaming
- **Whisper** — transcribes speech locally on GPU
- **Kokoro / ElevenLabs** — converts AI responses back to speech
- **Supabase + pgvector** — stores memories as semantic vectors (the "brain")
- **OpenRouter** — routes requests to Claude, GPT, or Gemini
- **Docker** — runs everything together

Full repo on GitHub: [link]

---

## Section 5: What Makes the Memory System Interesting
Most AI tools treat each conversation as a blank slate. This one stores every session as vector embeddings in a database and retrieves relevant memories before every response using semantic similarity search.

When I ask "do you remember what I told you about my job?" — it searches 1,536-dimensional vector space for the closest match to that query and injects it into the conversation. That's not a gimmick. That's how the good commercial products will work in 3 years.

---

## Section 6: What's Next
- iOS app (currently working through a browser, native app is next)
- MCP tool integrations (calendar, web search, home automation)
- Experimenting with running larger models locally as GPU hardware improves

---

## Closing
The point isn't the code. The point is that a person with no technical background can now build infrastructure that would have required a team of engineers five years ago. We're at a genuinely strange inflection point. I'm just trying to document what that actually looks like from the inside.

**GitHub:** [link]  
**If you try to build this:** [contact/comment]

---

*Tags: AI, Self-Hosted, Voice AI, Artificial Intelligence, No-Code, LLM, Personal AI*
