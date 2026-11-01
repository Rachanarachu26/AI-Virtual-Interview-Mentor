# ---- Backend image: FastAPI + Gemini + Whisper + MediaPipe ----
FROM python:3.11-slim

ENV PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1

# System libraries:
#   ffmpeg            -> required by Whisper to decode audio
#   libgl1/libglib2.0 -> required by OpenCV / MediaPipe
#   build-essential   -> safety net for any source builds
RUN apt-get update && apt-get install -y --no-install-recommends \
        ffmpeg \
        libgl1 \
        libglib2.0-0 \
        build-essential \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Install Python deps first (better layer caching).
COPY requirements.txt .
# openai-whisper builds from source and its setup.py imports pkg_resources,
# which setuptools >= 81 removed. Pip's isolated build env would otherwise pull
# the latest setuptools, so we: (1) pin a compatible setuptools in the main env,
# (2) install everything except whisper normally, (3) build whisper with
# --no-build-isolation so it reuses the main env's setuptools.
RUN pip install --upgrade pip "setuptools<81" wheel \
    # CPU-only PyTorch first, from PyTorch's CPU index. Otherwise Whisper pulls
    # the default CUDA build of torch (~1.5 GB of unused NVIDIA libraries).
    && pip install --index-url https://download.pytorch.org/whl/cpu "torch==2.2.2" \
    # Everything except Whisper (torch is now already satisfied, CPU build).
    && grep -v -i "openai-whisper" requirements.txt > /tmp/req-core.txt \
    && pip install -r /tmp/req-core.txt \
    # Whisper without build isolation so it reuses the pinned setuptools.
    && pip install --no-build-isolation "openai-whisper==20240930"

# App code.
COPY . .

EXPOSE 8000

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
