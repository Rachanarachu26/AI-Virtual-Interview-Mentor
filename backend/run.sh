#!/usr/bin/env bash
# One-command backend runner (macOS / Linux).
# Creates a virtual environment, installs dependencies, and starts the API.
set -e
cd "$(dirname "$0")"

echo "==> Setting up Python virtual environment..."
python3 -m venv .venv 2>/dev/null || true
# shellcheck disable=SC1091
source .venv/bin/activate

echo "==> Installing backend dependencies (this can take several minutes the first time"
echo "    because Whisper/PyTorch and MediaPipe are large)..."
pip install --quiet --upgrade pip
# Fix for openai-whisper's source build needing pkg_resources on newer setuptools.
echo "setuptools<81" > .pip-constraints.txt
PIP_CONSTRAINT=.pip-constraints.txt pip install -r requirements.txt
rm -f .pip-constraints.txt

echo "==> Starting FastAPI on http://localhost:8000  (docs at /docs)"
uvicorn app.main:app --reload --port 8000
