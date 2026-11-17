# Integration Test Pipeline Specification

## 1. Scope and Architecture

The integration test pipeline verifies end-to-end interactions between the FastAPI application, background workers, PostgreSQL 16 (with `pgvector`), Redis 7, and local mock S3 storage.

Integration tests are separated from fast unit tests using the pytest marker `integration`. They run in a dedicated, blocking job in `.github/workflows/ci.yml`.

```mermaid
flowchart LR
    Job[GitHub Actions: integration job] --> PG[(PostgreSQL Service: pgvector/pgvector:pg16)]
    Job --> RD[(Redis Service: redis:7)]
    Job --> TestRunner[pytest -m 'integration and not frozen']
    TestRunner --> TestDB[Postgres Migrations & Repositories]
    TestRunner --> TestQueue[Celery Redis Queue Broker]
    TestRunner --> TestStorage[Storage Adapters & Uploads]
```

## 2. CI Service Container Configuration

In `.github/workflows/ci.yml`, the integration job provisions ephemeral service containers on the GitHub Actions runner:

```yaml
services:
  postgres:
    image: pgvector/pgvector:pg16
    env:
      POSTGRES_USER: fashx
      POSTGRES_PASSWORD: fashx
      POSTGRES_DB: fashx_test
    ports: ["5432:5432"]
    options: >-
      --health-cmd "pg_isready -U fashx -d fashx_test"
      --health-interval 5s
      --health-timeout 5s
      --health-retries 10
  redis:
    image: redis:7
    ports: ["6379:6379"]
```

## 3. Environment Injections

The following environment variables are supplied to the integration runner:

```bash
DATABASE_URL=postgresql+asyncpg://fashx:fashx@localhost:5432/fashx_test
TEST_DATABASE_URL=postgresql+psycopg://fashx:fashx@localhost:5432/fashx_test
REDIS_URL=redis://localhost:6379/0
AUTH_JWT_SECRET=ci-test-jwt-secret-key-32-chars-minimum
AUTH_ISSUER=fashx-test
AUTH_AUDIENCE=fashx-api
```

## 4. Test Isolation and Cleanliness

1. Every test file under `tests/integration/` is automatically tagged with the `integration` marker in `tests/conftest.py`.
2. Tests that interact with the database use isolated transactional sessions or clean truncation to prevent test pollution between cases.
3. Tests that interact with Redis use key prefixes or Redis database flushing (`FLUSHDB`) in test fixtures.
4. Database tests (`-m db`) assert that 0 tests are skipped when Postgres is available.
