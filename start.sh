#!/usr/bin/env bash
set -e

# Render sets PORT automatically; fallback for local
export PORT=${PORT:-8000}

# Start FastAPI app (which also starts the Telegram bot on startup)
uvicorn app.webapp:app --host 0.0.0.0 --port "$PORT"
