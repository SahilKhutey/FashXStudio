# Database Migration Standard

**Status:** Adopted
**Version:** 1.0
**Effective Date:** 2026-11-11
**Category:** Engineering Architecture

---

## 1. Purpose and Scope

FashXStudio uses Alembic for relational database schema version control against PostgreSQL (with the `pgvector` extension). This standard outlines mandatory practices for creating, reviewing, testing, and deploying database migrations without causing service outages, lock contention, or data loss.

---

## 2. Core Governance Rules

1. **No Manual Schema Modifications:** Never alter a staging or production schema manually. All structural changes must occur through Alembic.
2. **Immutability of Merged Migrations:** Never edit or delete an Alembic migration that has been merged into `main` or executed against staging/production. Any fix or evolution must be submitted as a new migration file.
3. **Migration for Every Model Change:** Any modification to SQLAlchemy models under `backend/fashx/models/` requires a corresponding Alembic migration (`AGENTS.md` Rule 5).
4. **Meaningful Naming:** Use sequential revision prefixes with descriptive lowercase names:
   ```text
   alembic/versions/<revision>_<short_description>.py
   ```
   Examples:
   - `0026_add_vto_result_metadata.py`
   - `0027_add_catalog_source_provenance.py`
   - `0028_add_merchant_feature_settings.py`
5. **No Customer Data in Fixtures:** Never embed production or customer data, real names, or real photograph URLs in migration data scripts.
6. **Reversibility:** Every migration must provide both `upgrade()` and `downgrade()` methods, tested to ensure complete reversibility wherever mathematically and structurally possible.
7. **Atomic Operations:** Keep migrations focused. Do not combine unrelated table modifications in a single migration script.

---

## 3. Safe Migration Strategy: Expand → Migrate → Contract

Directly altering a schema in a way that breaks running application instances leads to downtime. FashXStudio requires the **Expand-Migrate-Contract** pattern for non-trivial schema evolutions:

```text
┌─────────────────┐       ┌─────────────────┐       ┌─────────────────┐
│     Phase 1     │       │     Phase 2     │       │     Phase 3     │
│     EXPAND      │  ───► │     MIGRATE     │  ───► │    CONTRACT     │
└─────────────────┘       └─────────────────┘       └─────────────────┘
  Add new columns           Deploy new code           Drop deprecated
  or tables as              writing to new model;     columns/tables
  nullable. Old code        backfill data in          after old code
  continues working.        controlled batches.       is uninstalled.
```

### Detailed Phases

1. **Phase 1: Expand**
   - Add new columns as `nullable=True` (or with safe non-locking defaults).
   - Add new tables or auxiliary relations.
   - Do not drop columns, rename columns, or add restrictive non-null constraints yet.
   - Deploy Phase 1 migrations. Existing application code continues running uninterrupted.

2. **Phase 2: Migrate**
   - Deploy updated application code that reads from both old/new schemas and writes to the new schema.
   - Run asynchronous batch jobs to backfill historical data from old fields to new fields.
   - Verify data consistency and confirm all services operate on the new schema.

3. **Phase 3: Contract**
   - Deploy code that relies exclusively on the new schema.
   - Add `nullable=False` constraints (if desired) now that all records are populated.
   - Remove obsolete columns, tables, or triggers in a final cleanup migration.

---

## 4. Preventing Lock Contention on PostgreSQL

PostgreSQL executes schema modifications under table locks (`ACCESS EXCLUSIVE`). On tables with active read/write traffic (e.g., `tryon_jobs`, `products`, `users`):

1. **Avoid Table Rewrites:** Adding a column with a dynamic default value (e.g., `DEFAULT clock_timestamp()`) rewrites the table. In modern PostgreSQL (11+), constant defaults do not rewrite tables.
2. **Concurrent Index Creation:** Indexes on large tables must be created concurrently (`op.create_index(..., postgresql_concurrently=True)`) inside a migration marked with `autocommit_block=True` to prevent blocking concurrent writes.
3. **Short Statement Timeouts:** Set a short `statement_timeout` on migrations affecting high-traffic tables so that a lock contention aborts rather than queues and starves all incoming queries.

---

## 5. Mandatory Migration Validation Cycle

Per `AGENTS.md` Rule 5 and Rule 13, every migration must be tested against a dedicated PostgreSQL database:

```bash
# 1. Verify single head revision (no multiple heads)
python -m alembic heads

# 2. Upgrade to the latest revision
python -m alembic upgrade head

# 3. Roll back one revision to verify downgrade capability
python -m alembic downgrade -1

# 4. Re-apply the upgrade to head
python -m alembic upgrade head

# 5. Check model-to-database parity (ensures no unmigrated SQLAlchemy model changes)
python -m alembic check
```

> **Verification Notice:** Running `alembic upgrade head --sql` (dry-run SQL generation) is not valid verification (`AGENTS.md` Rule 13). Validation must be executed against a running PostgreSQL instance with `pgvector` enabled (e.g., in CI or a local PostgreSQL container).
