#!/usr/bin/env bash
set -euo pipefail

python -m compileall -q api database schemas tests
python -m pytest -q
python -m alembic upgrade head --sql >/tmp/ai-fashion-assistant-foundation-1.sql

echo "Foundation 1 verification passed"
