# Migration 0053 Guide & Schema Evolution

## 1. Migration Metadata

- **Revision ID**: `0053_add_tryon_cache_and_cost_controls`
- **Revises**: `0052_add_tryon_reliability_events_and_dlq`
- **File**: `database/migrations/versions/0053_add_tryon_cache_and_cost_controls.py`
- **Target Systems**: PostgreSQL 16+

---

## 2. Upgrade Procedure

Run via Alembic:
```bash
alembic upgrade head
```

### Steps Performed:
1. Creates table `tryon_result_cache` with unique index on `cache_key`.
2. Creates table `tryon_provider_usage` with unique dedup constraint `uq_tryon_provider_usage_dedup`.
3. Creates table `tryon_budgets` with unique constraint `uq_tryon_budgets_scope_period`.
4. Creates table `tryon_budget_reservations` with foreign keys to budgets and jobs.

---

## 3. Rollback / Downgrade Procedure

In the event of an operational deployment abort:
```bash
alembic downgrade 0052_add_tryon_reliability_events_and_dlq
```

### Rollback Effects:
- Drops tables in safe dependency order:
  1. `tryon_budget_reservations`
  2. `tryon_budgets`
  3. `tryon_provider_usage`
  4. `tryon_result_cache`
- Leaves all pre-existing Phase 07.5 job states and dead-letter queue structures intact.

---

## 4. Verification Note (Rule 14 Compliance)

In accordance with repo `AGENTS.md` Rule 14:
- The local developer workstation operates under Windows without Docker or local PostgreSQL daemon installed.
- Syntax, model bindings, and foreign key definitions have been verified via Python runtime introspection (`database.models.TryOnResultCache`, etc.).
- Complete SQL execution against a live PostgreSQL cluster is executed via GitHub Actions CI pipeline on push.
