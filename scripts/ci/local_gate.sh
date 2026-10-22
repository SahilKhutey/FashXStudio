#!/usr/bin/env bash
set -euo pipefail
: "${TEST_DATABASE_URL:?set TEST_DATABASE_URL; the database name must end in _test}"
export DATABASE_URL="${DATABASE_URL:-$TEST_DATABASE_URL}"
ruff check .
mypy .
python scripts/docs_lint.py
python -m alembic heads
python -m alembic upgrade head
python -m alembic downgrade -1
python -m alembic upgrade head
python -m alembic check
set -o pipefail
python -m pytest tests -m db -q -rs | tee /tmp/db.log
if grep -q "SKIPPED" /tmp/db.log; then echo "db tests were skipped"; exit 1; fi
python -m pytest tests -q -p no:cacheprovider -m "not frozen"
echo "LOCAL GATE: ALL GREEN"
