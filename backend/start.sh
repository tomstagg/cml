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
python -c "from alembic.config import main; main()" upgrade head

echo "--- Starting uvicorn ---"
exec python -c "import uvicorn; uvicorn.run('app.main:app', host='0.0.0.0', port=int('${PORT:-8000}'))"
