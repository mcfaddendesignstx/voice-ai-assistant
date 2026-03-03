FROM python:3.12-slim

WORKDIR /app

# System deps for audio processing
RUN apt-get update && \
    apt-get install -y --no-install-recommends gcc libffi-dev && \
    rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

# "start" tells livekit-agents CLI to connect and wait for sessions
CMD ["python", "agent.py", "start"]
