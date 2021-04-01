#! /usr/bin/env bash
set -e

python /app/app/backend_pre_start.py

# Run migrations
alembic upgrade head

bash ./scripts/test.sh "$@"
