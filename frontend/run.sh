#!/usr/bin/env bash
# One-command frontend runner (macOS / Linux).
set -e
cd "$(dirname "$0")"

echo "==> Installing frontend dependencies..."
npm install

echo "==> Starting the app on http://localhost:5173"
npm run dev
