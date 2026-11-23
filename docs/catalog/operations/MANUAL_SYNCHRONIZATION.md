# Manual Synchronization

## 1. Overview
Merchant operators often need to trigger immediate catalog synchronization after updating inventories, launching seasonal campaigns, or fixing product feed errors. The manual synchronization engine provides idempotent, rate-limited, and traceable on-demand sync execution.

---

## 2. Synchronization Modes

```mermaid
graph TD
    Trigger([POST /api/v1/merchant/sources/{id}/sync]) --> ModeCheck{Select Mode}
    ModeCheck -->|INCREMENTAL| Inc[Fetch changes since last checkpoint timestamp/cursor]
    ModeCheck -->|FULL| Full[Scan full feed, refresh prices, detect discontinued products]
    ModeCheck -->|VALIDATION_ONLY| Val[Fetch sample & dry-run validation without publishing]
    Inc & Full & Val --> Exec[Enqueue IngestRun in 'queued' state]
```

1. **`INCREMENTAL`** (Default):
   - Leverages `catalog_sync_checkpoints` watermark.
   - Fetches only records created or modified since the last successful sync run.
   - Fastest mode with minimal external API load.
2. **`FULL`**:
   - Disregards incremental watermarks.
   - Re-scans all products from the merchant source.
   - Updates prices, availability, and identifies missing products to mark as out of stock.
3. **`VALIDATION_ONLY`**:
   - Executes fetch, schema validation, and normalization steps.
   - Bypasses persistence to `canonical_garments` and `merchant_offers`.
   - Used by merchants to verify newly connected feeds or modified schemas before production ingestion.

---

## 3. Idempotency and Deduplication Guarantee
To protect merchants and upstream retailer APIs from duplicate submissions caused by client network retries or accidental double-clicks:
- The merchant can supply an `idempotency_key` in the request header or JSON payload.
- If a sync run with the same `source_id` and `correlation_id` exists in the system:
  - FashXStudio returns the existing `IngestRun` record.
  - The response sets `is_duplicate_request: true`.
  - No redundant worker job is enqueued.

---

## 4. Concurrency Protection & Rate Limits
- Only one active synchronization job (`running`, `queued`, or `validating`) may run per catalog source at any given time.
- If a sync job is already in progress, subsequent requests fail with `409 Conflict` (`sync_already_running`).
- Operators can pass `force: true` to override concurrency locks only when an existing job has stalled beyond heartbeat timeout limits.
