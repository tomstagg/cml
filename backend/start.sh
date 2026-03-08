#!/bin/bash
set -e

echo "=== CML Backend Starting ==="
echo "PATH: $PATH"
echo "PORT: $PORT"
echo "ENVIRONMENT: $ENVIRONMENT"
echo "DATABASE_URL prefix: ${DATABASE_URL:0:40}..."

echo "--- Python location ---"
which python || echo "python not found in PATH"
python --version

echo "--- Running migrations ---"
python -m alembic upgrade head

echo "--- Starting uvicorn ---"
exec python -m uvicorn app.main:app --host 0.0.0.0 --port "${PORT:-8000}"
