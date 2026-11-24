# Phase 07.6 — Caching and Cost Controls

## 1. Executive Summary

Phase 07.6 establishes production caching, cost controls, rate limits, provider usage ledgers, and multi-tier budget safeguards for FashXStudio's Virtual Try-On (VTO) pipeline.

Virtual try-on inference incurs tangible third-party operational costs (e.g. FASHN API credits). Uncontrolled retries, repeated requests for identical inputs, concurrent request flooding, or runaway worker loops pose direct financial and operational risks. 

Phase 07.6 enforces six foundational architectural invariants:
1. **Deterministic Cache Fingerprinting**: Exact canonical SHA-256 hash across the requesting shopper, canonical product, raw image hashes, version tags, provider configurations, and output options.
2. **Strict Shopper Isolation**: Cached results contain private shopper visual data. Results are **never** shared across distinct user accounts, even for identical garments.
3. **Fail-Closed Budgeting with Atomic Pre-Reservations**: Cost reservations occur atomically in PostgreSQL *before* third-party inference requests are dispatched. Parallel workers cannot overshoot budget limits.
4. **Granular Usage Ledger with Strict Idempotency**: Every billable provider operation (`SUBMIT`, `POLL`, `DOWNLOAD`) is recorded with deduplication against provider request IDs.
5. **Comprehensive Rate Limiting**: Dual-tier sliding window limiters protect platform resources: shopper limits (5/10 min, 20/day, 2 concurrent) and merchant limits (60/min, 20 concurrent).
6. **Continuous Invalidation and Consent Compliance**: Takedowns, merchant catalog edits, or shopper consent revocations immediately invalidate cached assets.

---

## 2. System Architecture

```
                             +------------------------+
                             |  Shopper / Mobile App  |
                             +-----------+------------+
                                         |
                                         v
                             +------------------------+
                             |     VTO Router / API   |
                             +-----------+------------+
                                         |
                +------------------------+------------------------+
                |                                                 |
                v                                                 v
   +-------------------------+                       +-------------------------+
   |   User & Merchant Rate  |                       |   Shopper Authorization |
   |   Limits (Redis / Lua)  |                       |   & Consent Validation  |
   +------------+------------+                       +------------+------------+
                |                                                 |
                +------------------------+------------------------+
                                         v
                             +------------------------+
                             |   Cache Key Identity   |
                             |   SHA-256 Fingerprint  |
                             +-----------+------------+
                                         |
                                         v
                               /--------------------\
                              /   Cache Hit in DB    \
                             <   (Active & Valid)?    >
                              \                      /
                               \--------------------/
                                 /                \
                       Yes      /                  \  No (Cache Miss)
                               v                    v
                 +-----------------------+   +-----------------------------+
                 | Authorize Cache Record|   | Atomic Budget Reservation   |
                 | (Owner + Consent +    |   | (Platform / Merchant / User)|
                 |  Takedown Validation) |   +--------------+--------------+
                 +-----------+-----------+                  |
                             |                              v
                             v               +-----------------------------+
                 +-----------------------+   | Worker Inference Dispatch   |
                 | Return Cached Result  |   | (FASHN Provider Adapter)    |
                 | (Record Telemetry)    |   +--------------+--------------+
                 +-----------------------+                  |
                                                            v
                                             +-----------------------------+
                                             | Provider Usage Ledger       |
                                             | (tryon_provider_usage)      |
                                             +--------------+--------------+
                                                            |
                                                            v
                                             +-----------------------------+
                                             | Settle Budget Reservation   |
                                             | & Store in Result Cache     |
                                             +-----------------------------+
```

---

## 3. Implementation Roadmap & Milestones

| Milestone | Scope | Engineering Deliverables |
|---|---|---|
| **07.6-A** | Repository Audit & Schema Mapping | Architecture assessment, gap analysis, schema design. |
| **07.6-B** | Cache Identity & Shopper Isolation | `TryOnCacheIdentity`, canonical SHA-256 key, owner isolation, TTLs, invalidation handlers. |
| **07.6-C** | Usage Ledger & Cost Accounting | `TryOnProviderUsage` ledger, idempotency dedup, cost calculation service. |
| **07.6-D** | Rate Limiting & Concurrency Controls | Atomic Redis sliding window limiters, user limits, merchant limits, 429 semantics. |
| **07.6-E** | Global Budgets & Atomic Reservations | Multi-tier budgets (Platform/Merchant/User), atomic pre-reservations, `SUBMISSION_UNKNOWN` handling. |
| **07.6-F** | Database Models & Migration 0053 | SQLAlchemy models (`tryon_result_cache`, `tryon_provider_usage`, `tryon_budgets`, `tryon_budget_reservations`), Alembic migration `0053`. |
| **07.6-G** | Monitoring & Anomaly Detection | Prometheus non-PII metrics, budget threshold alerts (70%, 90%, 100%), spend spike detection. |
| **07.6-H** | Test Suites & Verification | 100% unit and integration test coverage across cache, rate limits, budgets, and usage accounting. |
| **07.6-I** | Production Engineering Documentation | 17 technical specifications covering all facets of Phase 07.6. |
| **07.6-J** | Linting, Gate Verification & Push | `ruff`, `mypy`, documentation linting, test suite execution, git push. |
