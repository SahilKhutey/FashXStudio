# Ingestion Quarantine

## 1. Purpose and Architecture

The ingestion quarantine system captures non-compliant, malformed, or unmapped product records so they can be reviewed, corrected, and reprocessed without failing entire synchronization batches.

---

## 2. Table Schema (`catalog_ingestion_quarantine`)

```sql
CREATE TABLE catalog_ingestion_quarantine (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    ingest_run_id UUID REFERENCES catalog_ingest_runs(id) ON DELETE SET NULL,
    source_id UUID NOT NULL REFERENCES catalog_sources(id) ON DELETE CASCADE,
    source_product_id VARCHAR(255),
    reason_code VARCHAR(64) NOT NULL,
    field_name VARCHAR(64),
    raw_record JSONB NOT NULL,
    status VARCHAR(32) NOT NULL DEFAULT 'PENDING',
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    resolved_at TIMESTAMPTZ,
    resolution_notes TEXT,
    CONSTRAINT uq_quarantine_source_prod_reason UNIQUE (source_id, source_product_id, reason_code)
);
```

---

## 3. Security & Sanitization Rules

1. **Secret Redaction**: Raw records stored in quarantine are sanitized. API tokens, Basic Auth headers, and presigned query strings are scrubbed.
2. **Idempotent Upsert**: Duplicate quarantine occurrences update the existing quarantine record timestamp and payload rather than creating redundant rows.
3. **Reprocessing**: Administrative endpoints allow re-evaluating quarantined items once mapping dictionaries or source configurations are corrected.
