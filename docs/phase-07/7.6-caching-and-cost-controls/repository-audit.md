# Phase 07.6 Repository Audit & Gap Analysis

## 1. Audit Scope & Objectives

This audit evaluates existing caching, rate limiting, cost tracking, and budget enforcement mechanisms across FashXStudio to inform the implementation of **Phase 07.6 — Caching and Cost Controls**.

The target requirements:
1. Prevent redundant paid third-party VTO inference via deterministic cache fingerprinting.
2. Protect shopper visual privacy through strict single-user cache partition and zero cross-user sharing.
3. Track billable provider actions with exact idempotency and granular per-operation cost accounting.
4. Safeguard platform and merchant finances via atomic pre-inference budget reservations.
5. Protect system availability with distributed sliding window rate limits.

---

## 2. Existing Baseline Code Assessment

### 2.1 Caching Logic
- **Existing File**: `backend/fashx/tryon/cache_key.py`
  - Currently defines `compute_tryon_cache_key(...)`.
  - **Gaps Identified**:
    - Missing `user_id` in the hash formula! Without `user_id` bound into the key or query filter, results could theoretically collide or leak between shoppers.
    - Missing `preprocessing_version`, `policy_version`, and normalized `output_options`.
    - No database-backed cache record (`tryon_result_cache`).
    - No automatic invalidation hooks for catalog takedowns, image changes, or consent revocations.

### 2.2 Cost Tracking & Usage
- **Existing Model**: `TryOnUsage` in `database/models/tryon.py`
  - Stores high-level job execution metrics (`provider`, `model`, `outcome`, `latency_ms`, `cost_usd_est`).
  - Deliberately omits `user_id` and `job_id` for privacy.
  - **Gaps Identified**:
    - Lacks granular operation tracking (`SUBMIT`, `POLL`, `DOWNLOAD`).
    - Lacks deduplication constraint against `provider_request_id` + `operation`.
    - Cannot track multi-attempt costs or billable polling calls.
    - No budget reservation linkages.

### 2.3 Rate Limiting
- **Existing Logic**:
  - Redis connection utilities exist in infrastructure modules.
  - FastAPI dependency injection does not currently enforce VTO-specific sliding window limits.
  - **Gaps Identified**:
    - No per-shopper sliding window limiter (5 requests / 10 min, 20 requests / day).
    - No concurrency ceiling per shopper (max 2 in-flight jobs).
    - No per-merchant API limiter (60 requests / min, max 20 concurrent).
    - Missing standardized `429 Too Many Requests` response headers (`Retry-After`, `X-RateLimit-*`).

### 2.4 Budgets and Reservations
- **Existing Logic**: None.
  - Jobs are dispatched directly to Celery workers without financial pre-authorization.
  - **Gaps Identified**:
    - No multi-tier budget definitions (Platform, Merchant, User).
    - No atomic pre-reservation mechanism; concurrent workers can execute inference even when budget is depleted.
    - No handling of uncertain submissions (`SUBMISSION_UNKNOWN`) where provider charges may occur despite network drops.

---

## 3. Required Deliverables Matrix

| Area | New Files / Modifications | Functionality |
|---|---|---|
| **Cache Keys** | `backend/fashx/tryon/cache/keys.py` | `TryOnCacheIdentity`, canonical SHA-256 fingerprinting. |
| **Cache Service** | `backend/fashx/tryon/cache/service.py` | Cache lookup, store, owner authorization, hit metrics. |
| **Cache Expiry & Invalidation** | `backend/fashx/tryon/cache/expiry.py`<br>`backend/fashx/tryon/cache/invalidation.py` | 7-day TTL, takedown triggers, consent revocations. |
| **Provider Usage** | `backend/fashx/tryon/billing/usage.py` | `TryOnProviderUsageService`, idempotency dedup. |
| **Cost Service** | `backend/fashx/tryon/billing/cost_service.py` | Per-job cost calculations, savings calculation. |
| **Rate Limiter** | `backend/fashx/tryon/limits/redis_limiter.py`<br>`backend/fashx/tryon/limits/user_limits.py`<br>`backend/fashx/tryon/limits/merchant_limits.py` | Sliding window limiter, Lua atomic scripts, 429 handlers. |
| **Budgets & Reservations** | `backend/fashx/tryon/billing/budget_service.py`<br>`backend/fashx/tryon/billing/reservations.py` | Platform/Merchant/User budgets, atomic compare-and-set reservation. |
| **Monitoring** | `backend/fashx/tryon/monitoring/metrics.py`<br>`backend/fashx/tryon/monitoring/anomaly_detection.py` | Prometheus metrics, 70/90/100% threshold alerts. |
| **Database Schema** | `database/models/tryon.py`<br>`database/migrations/versions/0053_add_tryon_cache_and_cost_controls.py` | New tables: `tryon_result_cache`, `tryon_provider_usage`, `tryon_budgets`, `tryon_budget_reservations`. |
