# Qwen3-TTS with PyTorch SM_120 (Blackwell/RTX 5090) support.
#
# qwen-tts pulls its own PyTorch. We install it first, then force-reinstall
# PyTorch cu128 on top so SM_120 CUDA kernels are present.
FROM python:3.12-slim

WORKDIR /app

# System deps for soundfile + audio encoding
RUN apt-get update && apt-get install -y --no-install-recommends \
    libsndfile1 ffmpeg && \
    rm -rf /var/lib/apt/lists/*

# Core deps
RUN pip install --no-cache-dir \
    fastapi uvicorn[standard] soundfile numpy pydantic

# Qwen3-TTS (may bring its own PyTorch)
RUN pip install --no-cache-dir qwen-tts

# Force-reinstall PyTorch with cu128 for RTX 5090 (SM_120)
RUN pip install --no-cache-dir --force-reinstall \
    torch torchaudio \
    --index-url https://download.pytorch.org/whl/cu128

# Verify CUDA/SM_120 support
RUN python -c "\
import torch; \
print('PyTorch:', torch.__version__); \
print('CUDA:', torch.version.cuda); \
print('CUDA available:', torch.cuda.is_available())"

# COPY last so server.py edits don't invalidate heavy cache layers above
COPY server.py .

EXPOSE 8890

CMD ["python", "server.py"]
