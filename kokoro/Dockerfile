# Custom Kokoro TTS image with PyTorch SM_120 (Blackwell/RTX 5090) support.
#
# The official kokoro-fastapi-gpu image ships PyTorch compiled for sm_50-sm_90.
# RTX 5090 is SM_120 and needs PyTorch built with cu128 CUDA support.
# This Dockerfile takes the GPU image and swaps in PyTorch nightly with cu128.

FROM ghcr.io/remsky/kokoro-fastapi-gpu:latest

# The base image uses uv (not pip) + a virtualenv at /app/.venv.
# Upgrade PyTorch to a build with SM_120 (Blackwell/RTX 5090) CUDA kernels.
ENV VIRTUAL_ENV=/app/.venv
RUN uv pip install --python /app/.venv/bin/python3 \
    torch torchaudio \
    --index-url https://download.pytorch.org/whl/cu128

# Verify CUDA/SM_120 support is present
RUN /app/.venv/bin/python3 -c "\
import torch; \
print('PyTorch:', torch.__version__); \
print('CUDA:', torch.version.cuda); \
print('CUDA available:', torch.cuda.is_available())"
