#!/bin/bash
set -e

echo "=== PSC Current Affairs Agent - Container Startup ==="

echo "[1/2] Initializing database..."
python scripts/init_db.py

echo "[2/2] Database ready."

echo "=== Starting: $@ ==="
exec "$@"
