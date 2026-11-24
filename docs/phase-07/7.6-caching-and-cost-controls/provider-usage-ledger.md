# Provider Usage Ledger & Cost Auditing

## 1. Accounting Philosophy

Virtual Try-On inference is an external API call with real financial liability. 
The database is the durable source of truth for billable vendor actions.

Every billable or metered interaction with inference providers (FASHN) is recorded in `tryon_provider_usage`.

### Core Rules:
1. **Granular Operations**: We track `SUBMIT`, `POLL`, `DOWNLOAD`, and `OTHER` as distinct rows.
2. **Strict Idempotency**: If a worker retries or re-polls a request that already has a `provider_request_id`, the ledger will not duplicate the charge record.
3. **Deterministic Unit Pricing**: Units consumed (credits) and unit price in USD are captured at the moment of execution.
4. **Linkage to Jobs**: Ledger records reference `tryon_job_id` with `ON DELETE SET NULL` so operational records persist even if temporary job records are cleaned up.

---

## 2. Table Schema (`tryon_provider_usage`)

```sql
CREATE TABLE tryon_provider_usage (
    id UUID PRIMARY KEY,
    tryon_job_id UUID REFERENCES tryon_jobs(id) ON DELETE SET NULL,
    provider VARCHAR(64) NOT NULL,
    provider_model VARCHAR(64),
    provider_request_id VARCHAR(255),
    operation VARCHAR(32) NOT NULL,
    status VARCHAR(32) NOT NULL,
    units_consumed NUMERIC(10, 4) NOT NULL DEFAULT 1.0000,
    unit_cost_usd NUMERIC(10, 4) NOT NULL DEFAULT 0.0000,
    total_cost_usd NUMERIC(10, 4) NOT NULL DEFAULT 0.0000,
    currency VARCHAR(8) NOT NULL DEFAULT 'USD',
    latency_ms INTEGER,
    http_status INTEGER,
    raw_usage_metadata JSONB NOT NULL DEFAULT '{}'::jsonb,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    CONSTRAINT uq_tryon_provider_usage_dedup UNIQUE (provider, provider_request_id, operation)
);
```

---

## 3. Idempotency & Deduplication

When a worker calls `TryOnProviderUsageService.record_usage()`, the service executes:

```python
if record.provider_request_id:
    existing = await session.execute(
        select(TryOnProviderUsage).where(
            TryOnProviderUsage.provider == record.provider,
            TryOnProviderUsage.provider_request_id == record.provider_request_id,
            TryOnProviderUsage.operation == record.operation.value,
        )
    )
    if existing.scalar_one_or_none():
        return existing
```

This prevents duplicate entries when network drops prompt identical poll attempts or when status checks are repeated.
