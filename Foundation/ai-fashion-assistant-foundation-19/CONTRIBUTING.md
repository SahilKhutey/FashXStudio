# Engineering Rules

1. Router code does not access repositories directly.
2. Application/use-case code orchestrates side effects.
3. Domain code does not import FastAPI, SQLAlchemy, Redis, R2, or vendor SDKs.
4. Repositories do not cross domain ownership boundaries.
5. External SDKs are used only behind ports/adapters.
6. Database changes require Alembic migrations.
7. Shared schemas are versioned and never copy-pasted between consumers.
8. Async jobs must be atomically claimed and idempotent.
9. Artifact/cache keys are distinct from request idempotency keys.
10. Sensitive media access is capability-scoped.
