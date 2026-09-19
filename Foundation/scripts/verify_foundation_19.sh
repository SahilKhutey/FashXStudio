#!/usr/bin/env bash
set -euo pipefail

python -m compileall -q api schemas database workers tests
pytest -q
python -m alembic upgrade head --sql >/tmp/ai-fashion-assistant-foundation-19.sql
printf 'Foundation 19 verification: PASS\n'
