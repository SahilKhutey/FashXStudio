# AI Fashion Assistant

Production-build baseline for the AI Fashion Assistant monorepo.

## Current build stage

**Foundation 1 — Shared Domain Contracts + Database Foundation**

Foundation 1 establishes the production-shaped contracts and persistence model that later MVP/V1 services implement.

### Included

- FastAPI application shell from Foundation 0
- Versioned Pydantic contracts under `/schemas`
- SQLAlchemy 2.x domain models
- Alembic migration chain
- PostgreSQL + pgvector extension foundation
- Profile/body/measurement contracts
- Merchant / garment / offer domain separation
- Image asset and enrichment model
- Try-On job/artifact model with version-aware identity
- Wardrobe / commerce / fit-feedback contracts
- Visual try-on feedback contracts
- Domain-event persistence model
- Contract + model unit tests

### Architecture rules

- Routers do not access the database directly.
- Application/domain code does not import infrastructure SDKs.
- Repositories do not cross domain ownership boundaries.
- Shared contracts live in `/schemas` and are versioned.
- Idempotency keys are distinct from artifact/cache keys.
- Raw user media remains in object storage, never Postgres.

## Local setup

```bash
cp .env.example .env
uv sync

docker compose up -d
uv run alembic upgrade head

uv run pytest
uv run ruff check .
uv run mypy api schemas database
```

API:

```text
http://127.0.0.1:8000
http://127.0.0.1:8000/api/v1/system/health/live
http://127.0.0.1:8000/api/v1/system/health/ready
```


## Foundation 10

Foundation 10 adds the curated discovery feed runtime and Expo mobile feed screen. See `docs-foundation-10.md`.
