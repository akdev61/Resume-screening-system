#!/usr/bin/env bash
set -e

echo "Starting entrypoint..."

# Wait for DB to be available (simple loop)
if [ -n "${DATABASE_URL}" ]; then
  echo "Waiting for database at ${DATABASE_URL}..."
  until python - <<PY >/dev/null 2>&1
import os
import sys
try:
    import psycopg2
    dsn = os.environ.get('DATABASE_URL')
    conn = psycopg2.connect(dsn)
    conn.close()
except Exception:
    sys.exit(1)
sys.exit(0)
PY
  do
    printf '.'
    sleep 1
  done
  echo "\nDatabase reachable"
fi

# Run Alembic migrations
if command -v alembic >/dev/null 2>&1; then
  echo "Running database migrations..."
  alembic -c alembic.ini upgrade head || true
fi

echo "Launching Uvicorn"
exec uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
