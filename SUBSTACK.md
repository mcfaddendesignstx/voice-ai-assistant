# READY-TO-PUBLISH POST (copy everything below the line)

---

# I Built a Voice AI That Remembers Everything — And I'm Not a Developer

I want to be upfront about something before you read any further: I did not write a single line of code in this project. Not one. Every piece of software you're about to read about was written by an AI while I sat across from it and described what I wanted.

I'm sharing this because I think what happened here matters — not the code, but what it represents.

---

I got tired of talking to ChatGPT.

Not because it isn't impressive. It is. But every time I opened a new conversation, it had forgotten everything. My name. My job. What we talked about the day before. I was starting from zero, every single time, with something I was starting to treat like a thinking partner.

And then there's the other thing — every word I say to it goes to OpenAI. I'm not particularly paranoid about that, but it started to bother me. The more personal and useful those conversations got, the more I thought about what I was handing over.

So I started asking a different question: *could I build something like this that was actually mine?*

---

I found Nate Jones on Substack — that's actually why I'm here. He had written about building a persistent memory system for AI using open-source tools and a vector database. The idea was that every conversation gets stored as a kind of fingerprint in a database, and when you talk to the AI again, it searches those fingerprints for anything relevant and injects them into the conversation before responding.

I didn't fully understand it. But I understood the concept: the AI would remember.

I decided to try to build it. Using an AI.

---

Here's what I actually built, in plain English:

A voice AI assistant that runs on my home PC. I talk to it through a browser on any device on my network. It hears me through Whisper (a speech recognition model that runs locally on my GPU), thinks through whatever AI model I've selected — Google Gemini, Claude, or GPT — and talks back using a voice synthesizer that also runs on my machine.

Every session gets summarized and stored in a database I control. The next time I connect, before it responds to anything I say, it searches that database for memories related to what I'm talking about and uses them to answer. It knows my name. It knows what I do for work. It knows about my family. It knows things I told it weeks ago.

Nothing leaves my house except the inference call to the AI model. The voice processing, the memory storage, the session routing — all local.

---

The actual building process was something I'm still processing.

I used an AI coding tool called Windsurf with an assistant called Cascade. I would describe what I wanted. It would write the code. I would test it, tell it what wasn't working, and we'd iterate. I made every architectural decision. I tested everything. I just didn't type the code.

It took weeks. There were things that broke repeatedly. There were times I didn't know how to describe what was wrong. But we got there.

I've been in healthcare for years. I'm not a software person. The closest I've come to coding before this is copy-pasting something from a forum to fix a problem on my computer. That's the context.

---

What I take away from this isn't "AI can build software for you." That's true but it's not the interesting part.

The interesting part is that the gap between having an idea and having a working system is now much smaller than it used to be. Not zero — this still took real time and effort and a lot of frustration. But the barrier used to be: *do you know how to code?* That's no longer the barrier.

The new barrier is: *do you know what you want, and can you describe it clearly enough?*

That's a different skill. One that I think a lot of people already have.

---

The full code is on GitHub if you want to build this yourself: **[link]**

Fair warning: you need a PC with an NVIDIA GPU to run the local parts. The memory system uses Supabase (free tier works fine). The AI calls go through OpenRouter. There's a setup process that isn't trivial — but there's documentation, and if I could get through it, most people can.

I'll write more about the specific pieces as I keep building. There's a lot more I want to add.

---

*If you're technical and want to dig into how the memory system works specifically, I'll cover that in a follow-up. If you're not technical and you want to talk about the non-coder-builds-software angle, I'm more interested in that conversation anyway.*

---

# OUTLINE NOTES (for future posts)
- Follow-up 1: How the memory system actually works (vector embeddings explained simply)
- Follow-up 2: The model comparison — Gemini vs Claude vs GPT for voice conversation
- Follow-up 3: What I want to build next (MCP tools, iPhone app, home automation)
- Follow-up 4: The honest cost breakdown (hardware, API costs, time investment)

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
