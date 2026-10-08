# AI Fashion Assistant — Production Build Foundation 2

**Status:** Implemented  
**Purpose:** Shared application infrastructure: repositories, transaction boundaries, ports, typed errors, idempotency, and first application use cases.

## Delivered

- SQLAlchemy repository primitives and domain-owned repositories.
- Explicit transaction boundary with rollback on failure.
- Application-service layer for profile and catalog use cases.
- Dependency injection helpers for repositories.
- Typed application errors mapped to the standard API error envelope.
- Deterministic request fingerprinting.
- Database-backed idempotency records with conflict detection.
- Domain ports for storage, profile, catalog, and queues.
- Pure domain validation/versioning helpers.
- Alembic `0003_operations_and_vector_upgrade`.
- Normalization of vector columns to `VECTOR(512)`.

## Rules locked

1. Routers do not access repositories directly.
2. Application services orchestrate transactions and side effects.
3. Domain helpers remain infrastructure-free.
4. Repositories access only their owned persistence boundary.
5. External systems are represented through ports/adapters.
6. Idempotency keys are distinct from deterministic artifact/cache keys.
7. A reused idempotency key with a different request fingerprint is a conflict.
8. An in-progress duplicate is a conflict until the original operation completes.
9. Database changes occur only through Alembic migrations.
