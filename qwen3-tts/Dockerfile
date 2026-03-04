FROM python:3.12-slim

WORKDIR /app

# System deps for soundfile
RUN apt-get update && apt-get install -y --no-install-recommends \
    libsndfile1 ffmpeg && \
    rm -rf /var/lib/apt/lists/*

# Python deps
RUN pip install --no-cache-dir \
    fastapi uvicorn[standard] soundfile numpy pydantic \
    torch --index-url https://download.pytorch.org/whl/cu128

# Qwen3-TTS package
RUN pip install --no-cache-dir qwen-tts

COPY server.py .

EXPOSE 8890

CMD ["python", "server.py"]
