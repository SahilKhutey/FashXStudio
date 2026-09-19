.PHONY: test verify lint typecheck migration-sql

test:
	python -m pytest -q

verify:
	./scripts/verify_foundation_1.sh

lint:
	python -m ruff check .

typecheck:
	python -m mypy api schemas database

migration-sql:
	python -m alembic upgrade head --sql
