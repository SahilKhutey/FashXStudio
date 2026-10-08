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

## Foundation 12 — Commerce & Buy-Handoff

Implemented the MVP commerce boundary:

- `POST /api/v1/commerce/buy-click`
- trusted merchant-offer URL resolution
- configurable affiliate tracking adapter
- `buy_clicks` attribution persistence
- `buy_clicked` domain event persistence
- optional idempotency key handling

Verification: 61 pytest tests passed.
## Foundation 14 — Try-On Input Assembly & Provider Runtime

Foundation 14 adds the provider-neutral execution path for asynchronous virtual try-on.

- Validates the MVP garment category before GPU submission.
- Retrieves accepted user photo + compatible garment image through domain ports.
- Uses short-lived signed R2 URLs for provider inputs.
- Supports a generic HTTP provider behind `TryOnProvider`.
- Default provider remains `disabled` until a commercially approved model/provider is configured.
- Polls provider completion, validates the returned image, uploads it to `tryon-results/`, and completes the Try-On artifact.
- Enforces legal Try-On state transitions.

The public model/provider contract is deliberately vendor-neutral so a licensed production VTO backend can be introduced without changing mobile/API contracts.

