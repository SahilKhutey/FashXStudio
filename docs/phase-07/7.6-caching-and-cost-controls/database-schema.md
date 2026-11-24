# Database Schema: Caching, Usage, Budgets & Reservations

## 1. Relational Entity Overview

Phase 07.6 introduces four core PostgreSQL tables into the schema:

```
        +-----------------------------------+
        |            users                  |
        +-----------------+-----------------+
                          | 1:N
                          v
        +-----------------------------------+
        |       tryon_result_cache          |
        +-----------------+-----------------+
                          |
                          | N:1
                          v
        +-----------------------------------+
        |            tryon_jobs             |
        +-----------------+-----------------+
                          |
            +-------------+-------------+
            | 1:N                       | 1:N
            v                           v
+-------------------------+ +-------------------------+
|   tryon_provider_usage  | | tryon_budget_reservations|
+-------------------------+ +------------+------------+
                                         | N:1
                                         v
                            +-------------------------+
                            |      tryon_budgets      |
                            +-------------------------+
```

---

## 2. Table Specifications

### 2.1 `tryon_result_cache`
- Primary Key: `id` (UUID)
- Key Column: `cache_key` (VARCHAR(64), UNIQUE)
- Ownership: `owner_user_id` (UUID FK users.id)
- Target: `canonical_product_id` (UUID FK canonical_garments.id)
- Storage: `result_storage_uri` (TEXT), `result_sha256` (VARCHAR(64))
- TTL: `expires_at` (TIMESTAMPTZ), `metadata_expires_at` (TIMESTAMPTZ)
- Performance: Indexed by `cache_key`, `owner_user_id`, `canonical_product_id`, and `(status, expires_at)`.

### 2.2 `tryon_provider_usage`
- Primary Key: `id` (UUID)
- Link: `tryon_job_id` (UUID FK tryon_jobs.id ON DELETE SET NULL)
- Provider Info: `provider`, `provider_model`, `provider_request_id`, `operation`, `status`
- Financials: `units_consumed`, `unit_cost_usd`, `total_cost_usd`, `currency`
- Telemetry: `latency_ms`, `http_status`, `raw_usage_metadata` (JSONB)
- Constraint: `uq_tryon_provider_usage_dedup` on `(provider, provider_request_id, operation)`.

### 2.3 `tryon_budgets`
- Primary Key: `id` (UUID)
- Scope: `scope_type` (PLATFORM, MERCHANT, USER), `scope_id`
- Period: `period` (DAILY, MONTHLY), `period_start`, `period_end`
- Limits: `hard_limit_amount`, `warn_threshold_pct`, `crit_threshold_pct`
- Balances: `current_spend_usd`, `reserved_spend_usd`
- Constraint: `uq_tryon_budgets_scope_period` on `(scope_type, scope_id, period, period_start)`.

### 2.4 `tryon_budget_reservations`
- Primary Key: `id` (UUID)
- Links: `budget_id` (UUID FK tryon_budgets.id), `tryon_job_id` (UUID FK tryon_jobs.id)
- Amounts: `reserved_amount_usd`, `committed_amount_usd`
- Status: `status` (RESERVED, COMMITTED, RELEASED, TIMED_OUT, HELD_FOR_RECONCILIATION)
- Lifespan: `expires_at` (TIMESTAMPTZ)
