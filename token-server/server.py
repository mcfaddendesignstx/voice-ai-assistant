"""
Token Server — mints LiveKit JWTs for the iOS app.

The iOS app calls GET /token?room=<name>&identity=<name> before connecting
to the LiveKit server.  This keeps your API secret off the device.

Environment variables (from docker-compose):
  LIVEKIT_API_KEY
  LIVEKIT_API_SECRET
  LIVEKIT_EXTERNAL_URL  — the URL the iPhone should connect to
"""

import os

from fastapi import FastAPI, Query
from fastapi.middleware.cors import CORSMiddleware
from livekit.api import AccessToken, VideoGrants, RoomAgentDispatch, RoomConfiguration

app = FastAPI(title="LiveKit Token Server")

# Allow requests from any origin (iOS app, browser playground, etc.)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

API_KEY = os.environ["LIVEKIT_API_KEY"]
API_SECRET = os.environ["LIVEKIT_API_SECRET"]
EXTERNAL_URL = os.environ.get("LIVEKIT_EXTERNAL_URL", "ws://localhost:7880")


VALID_MODELS = {"gemini-flash", "claude-haiku", "gpt-4o-mini"}


@app.get("/token")
async def get_token(
    room: str = Query(default="voice-room", description="LiveKit room name"),
    identity: str = Query(default="iphone-user", description="Participant identity"),
    model: str = Query(default="gemini-flash", description="LLM model: gemini-flash | claude-haiku | gpt-4o-mini"),
):
    """
    Returns a JSON object the iOS app uses to connect:
      { "token": "<jwt>", "url": "ws://..." }
    """
    model = model if model in VALID_MODELS else "gemini-flash"

    token = (
        AccessToken(API_KEY, API_SECRET)
        .with_identity(identity)
        .with_grants(
            VideoGrants(
                room_join=True,
                room=room,
                can_publish=True,
                can_subscribe=True,
                can_publish_data=True,
            )
        )
        .with_room_config(
            RoomConfiguration(
                agents=[
                    RoomAgentDispatch(agent_name="voice-assistant", metadata=model)
                ],
            ),
        )
    )

    return {
        "token": token.to_jwt(),
        "url": EXTERNAL_URL,
        "model": model,
    }


@app.get("/health")
async def health():
    return {"status": "ok"}
