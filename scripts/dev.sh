#!/usr/bin/env bash
set -euo pipefail
export APP_ENV=${APP_ENV:-dev}
export PORT=${PORT:-8080}
uvicorn app.main:app --reload --port "$PORT" --host 0.0.0.0 --workers 1
