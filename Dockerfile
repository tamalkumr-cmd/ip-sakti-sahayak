# Place this file at the REPO ROOT (ip-sakti-sahayak/Dockerfile), next to
# the backend/ and ai_engine/ folders -- NOT inside backend/.
#
# Uses Docker (not Render's native Python runtime) specifically because the
# native runtime has no way to install system packages like ffmpeg, which
# pydub needs for voice transcription's audio format conversion.

FROM python:3.11-slim

# ffmpeg is required by backend/routers/voice_router.py (via pydub) to
# convert browser-recorded audio (webm/opus) into WAV before transcription.
# Without this, every real voice request fails on the server.
RUN apt-get update && \
    apt-get install -y --no-install-recommends ffmpeg && \
    rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Install Python dependencies first (separate layer so Docker caches this
# step and doesn't reinstall everything on every code change).
COPY backend/requirements.txt backend/requirements.txt
RUN pip install --no-cache-dir -r backend/requirements.txt

# Copy the whole repo, preserving the backend/ and ai_engine/ sibling
# structure that ai_bridge.py and docs_router.py rely on via relative paths.
COPY . .

WORKDIR /app/backend

# Render injects $PORT at runtime; must bind 0.0.0.0, not 127.0.0.1, so
# Render's proxy can route external traffic to the container.
CMD uvicorn main:app --host 0.0.0.0 --port $PORT