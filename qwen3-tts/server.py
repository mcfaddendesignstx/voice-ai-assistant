"""
Qwen3-TTS — OpenAI-compatible TTS wrapper.

Exposes POST /v1/audio/speech (same shape as Kokoro/OpenAI) so the LiveKit
agent can switch TTS engines with zero code changes.

Model: Qwen3-TTS-12Hz-0.6B-CustomVoice (smallest, fits alongside Whisper on a 5090).
"""

import io
import logging
import os
from contextlib import asynccontextmanager

import numpy as np
import soundfile as sf
import torch
import uvicorn
from fastapi import FastAPI, Request, Response
from fastapi.responses import StreamingResponse
from pydantic import BaseModel

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("qwen3-tts")

MODEL_NAME = os.getenv("QWEN3_TTS_MODEL", "Qwen/Qwen3-TTS-12Hz-0.6B-CustomVoice")
DEVICE = os.getenv("QWEN3_TTS_DEVICE", "cuda:0")
DEFAULT_SPEAKER = os.getenv("QWEN3_TTS_SPEAKER", "Ethan")
DEFAULT_LANGUAGE = os.getenv("QWEN3_TTS_LANGUAGE", "English")

# Speaker map: OpenAI-style voice names → Qwen3 speaker names
VOICE_MAP = {
    "ethan": "Ethan",
    "ryan": "Ryan",
    "vivian": "Vivian",
    "claire": "Claire",
    "laura": "Laura",
    "sophia": "Sophia",
    "chelsie": "Chelsie",
    "alloy": "Ethan",      # OpenAI alias
    "echo": "Ryan",        # OpenAI alias
    "nova": "Vivian",      # OpenAI alias
    "onyx": "Ethan",       # OpenAI alias
    "am_adam": "Ethan",    # Kokoro alias for seamless switching
}

model = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    global model
    logger.info("Loading Qwen3-TTS model: %s on %s", MODEL_NAME, DEVICE)
    from qwen_tts import Qwen3TTSModel
    model = Qwen3TTSModel.from_pretrained(
        MODEL_NAME,
        device_map=DEVICE,
        dtype=torch.bfloat16,
    )
    logger.info("Qwen3-TTS model loaded and ready")
    yield
    logger.info("Shutting down Qwen3-TTS")


app = FastAPI(title="Qwen3-TTS OpenAI-Compatible Server", lifespan=lifespan)


class SpeechRequest(BaseModel):
    model: str = "qwen3-tts"
    input: str
    voice: str = DEFAULT_SPEAKER
    response_format: str = "mp3"
    speed: float = 1.0


@app.post("/v1/audio/speech")
async def create_speech(req: SpeechRequest):
    """OpenAI-compatible TTS endpoint. Returns audio bytes."""
    if model is None:
        return Response(content="Model not loaded", status_code=503)

    speaker = VOICE_MAP.get(req.voice.lower(), DEFAULT_SPEAKER)
    text = req.input.strip()
    if not text:
        return Response(content="Empty input", status_code=400)

    logger.info("Generating speech: voice=%s speaker=%s text=%s", req.voice, speaker, text[:80])

    try:
        wavs, sr = model.generate_custom_voice(
            text=text,
            language=DEFAULT_LANGUAGE,
            speaker=speaker,
        )
    except Exception as e:
        logger.error("Generation failed: %s", e)
        return Response(content=f"Generation failed: {e}", status_code=500)

    audio_data = wavs[0]
    if isinstance(audio_data, torch.Tensor):
        audio_data = audio_data.cpu().numpy()

    buf = io.BytesIO()
    fmt = req.response_format.lower()
    if fmt == "wav":
        sf.write(buf, audio_data, sr, format="WAV")
        media_type = "audio/wav"
    elif fmt == "pcm":
        pcm = (audio_data * 32767).astype(np.int16)
        buf.write(pcm.tobytes())
        media_type = "audio/pcm"
    else:
        sf.write(buf, audio_data, sr, format="MP3")
        media_type = "audio/mpeg"

    buf.seek(0)
    return StreamingResponse(buf, media_type=media_type)


@app.get("/health")
async def health():
    return {"status": "ok", "model": MODEL_NAME, "ready": model is not None}


@app.get("/v1/audio/voices")
async def list_voices():
    """Return available voices for compatibility with Kokoro's voice listing."""
    return {"voices": list(VOICE_MAP.keys())}


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8890)
