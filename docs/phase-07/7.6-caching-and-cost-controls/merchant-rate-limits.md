# Merchant Rate Limiting & Catalog Concurrency

## 1. Merchant-Tier Limits

Merchants integrate with FashXStudio via catalog sync, bulk verification, or embedded widgets. To prevent any single merchant from starving cluster capacity or exhausting the global inference pool, merchant-level controls are enforced.

| Limit Type | Threshold | Window Duration | Description |
|---|---|---|---|
| **Short-Term Rate** | 60 Requests | 1 Minute (60s) | Protects provider ingestion queues. |
| **Concurrency Ceiling** | 20 Active Jobs | Real-time | Caps simultaneous inference across entire merchant catalog. |

---

## 2. Concurrency Leases

Merchant concurrency uses Redis Sets (`tryon:concurrency:merchant:{merchant_id}`):
- Before dispatching a new job, the worker/service attempts `acquire_concurrency(...)`.
- `SCARD` checks the current count against `MAX_CONCURRENT_JOBS` (20).
- If under limit, the job ID is added with a 300-second fallback TTL (protecting against unhandled worker crashes).
- Once the job reaches a terminal state (`COMPLETED`, `FAILED`, `CANCELLED`), `release_concurrency(...)` removes the job ID from the set.

---

## 3. Degradation & Overflow

If a merchant reaches either limit:
- Synchronous API submissions receive `429 Too Many Requests` with `X-RateLimit-Type: MERCHANT_CONCURRENCY`.
- Asynchronous batch ingestion jobs are re-queued with exponential backoff rather than dropped.
