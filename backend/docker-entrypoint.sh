#!/bin/sh
# CyberSathi backend entrypoint.
#   1. note whether this is a brand-new volume
#   2. apply migrations
#   3. seed the knowledge base / quiz bank / demo cohort, but only on first boot
#   4. serve
set -e

DB_PATH="${DATABASE_URL#sqlite:///}"

# Tested BEFORE migrating: alembic creates the file, so afterwards it always exists.
FRESH=0
if [ ! -f "$DB_PATH" ]; then
  FRESH=1
fi

echo "[cybersathi] applying migrations"
alembic upgrade head

if [ "$FRESH" = "1" ]; then
  echo "[cybersathi] first boot -- seeding knowledge base, quiz bank and demo cohort"
  python -m app.seed.run --all
else
  echo "[cybersathi] existing database at $DB_PATH -- skipping seed"
fi

echo "[cybersathi] starting API on 0.0.0.0:8000"
exec uvicorn app.main:app --host 0.0.0.0 --port 8000
