# RC08 — Database & Migrations

## 1. PostgreSQL Engine & Extension Baseline
- **Engine**: PostgreSQL 16.x
- **Required Extension**: `pgvector` (0.7.x+) for high-dimensional cosine similarity queries.
- **Connection Scheme**: `postgresql+asyncpg://` for application runtime; `postgresql+psycopg://` for Alembic migrations and synchronous CLI tools.
- **Connection Pooling**:
  - `pool_size`: 10 connections per container instance.
  - `max_overflow`: 5 connections.
  - `pool_recycle`: 1800 seconds (30 minutes).
  - `pool_pre_ping`: True (fail-fast dead connection detection).

## 2. Migration Discipline (Rule 5 & CI Verification)
Every database modification requires an Alembic migration tested against PostgreSQL:
1. `python -m alembic heads` (confirms single head).
2. `python -m alembic upgrade head` (applies all schema changes).
3. `python -m alembic downgrade -1` (verifies clean rollback).
4. `python -m alembic upgrade head` (re-applies to head).
5. `python -m alembic check` (detects unmigrated model attributes).

## 3. Disaster Recovery & Replication
- **WAL Archiving**: Continuous Write-Ahead Logging to private object storage.
- **Point-in-Time Recovery (PITR)**: 7-day retention window.
- **Automated Snapshots**: Daily snapshot retained for 30 days.
