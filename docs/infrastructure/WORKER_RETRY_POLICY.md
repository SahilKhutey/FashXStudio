# FashXStudio — Worker Retry & Resilience Policy (Phase 03.3)

## 1. Principles
Background worker failures must be handled deterministically:
1. **Transient failures** (network timeouts, broker blips, upstream API rate limits) must retry with exponential backoff and jitter.
2. **Deterministic failures** (invalid UUIDs, schema errors, business constraint violations, missing user consent) must fail fast without retrying to prevent resource exhaustion.
3. Every task execution must be strictly bounded by hard timeouts and maximum retry counts.

---

## 2. Classification of Errors

| Category | Exception Types | Action |
| :--- | :--- | :--- |
| **Transient (Retryable)** | `ConnectionError`, `TimeoutError`, `OSError`, `httpx.TimeoutException`, `httpx.TransportError`, HTTP 429, HTTP 502/503/504 | Retry with exponential backoff up to `max_retries`. |
| **Deterministic (Non-Retryable)** | `ValueError`, `TypeError`, `KeyError`, `EntityNotFoundError`, `ConsentRequiredError`, `ValidationError` | Do not retry. Immediately invoke failure callback and route to dead letter. |

---

## 3. Task Limits Matrix

| Task Name | Queue | Soft Timeout | Hard Timeout | Max Retries | Backoff Strategy |
| :--- | :--- | :--- | :--- | :--- | :--- |
| `process_tryon_job` | `tryon` | 105s | 115s | 3 | Exponential: `min(30, 2^retries)` seconds |
| `ingest_catalog_feed` | `ingest` | 480s | 600s | 3 | Exponential: `min(60, 2^retries * 5)` seconds |
| `enrich_garment_task` | `ingest` | 240s | 300s | 2 | Exponential: `min(30, 2^retries * 2)` seconds |
| `relay_outbox_events` | `maintenance` | 45s | 60s | 5 | Linear: `5` seconds |
| `sweep_storage_erasure` | `maintenance` | 120s | 150s | 3 | Linear: `10` seconds |
| `run_retention_jobs` | `maintenance` | 480s | 600s | 2 | Exponential: `60` seconds |

---

## 4. Visibility Timeout Invariant
The Celery broker transport visibility timeout is configured to:
```python
broker_transport_options = {"visibility_timeout": 300}
```
For `process_tryon_job` (hard limit 115s), the visibility timeout exceeds execution time by over 2.5x, guaranteeing that Redis will not redeliver an in-progress job to another worker while it is running normally.
