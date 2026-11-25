# Phase 07 Cache & Cost Controls Verification

## 1. Cost Management & Cache Principles

To prevent runaway spending on paid third-party AI inference while protecting privacy, FashXStudio implements:
1. **Deterministic Canonical Cache Keys**: Cached results are reused only when inputs and model configuration match identically.
2. **Strict Cache Isolation**: Cached assets are strictly scoped to the authenticated tenant. Cross-shopper cache sharing of generated images is strictly prohibited.
3. **Multi-Tier Spending Caps**: Granular limits per user, per merchant, and environment-wide, with a global emergency kill switch.
4. **Durable Usage Ledger**: Every provider attempt (success, failure, or cached) is logged for financial reconciliation.

---

## 2. Canonical Cache Key Specification

The cache key is computed as a SHA-256 hash of canonicalized input attributes (`backend/fashx/tryon/cache/keys.py`):

$$\text{CacheKey} = \text{SHA256}(\text{ShopperPhotoHash} \mathbin{\Vert} \text{GarmentImageHash} \mathbin{\Vert} \text{Category} \mathbin{\Vert} \text{ProviderVersion} \mathbin{\Vert} \text{PromptConfigHash})$$

### Invalidation Triggers:
- **Shopper Image Deletion**: Automatically purges all cache entries referencing that photo ID.
- **Merchant Takedown / Delisting**: Purges all cache entries referencing the garment asset ID.
- **Provider / Pipeline Upgrade**: Incrementing `provider_version` or `pipeline_version` automatically isolates new requests from legacy cache entries.
- **TTL Expiration**: Standard cache entries expire after 30 days (`TTL = 2,592,000s`).

---

## 3. Spending Controls & Quotas

| Control Level | Limit Threshold | Action on Exceeded Limit | Automated Test Reference |
| :--- | :--- | :--- | :--- |
| **Per-User Rate Limit** | Max 5 requests / 10 minutes | HTTP 429 Too Many Requests | `test_rate_limits.py` |
| **Per-User Daily Quota** | Max 20 try-ons / day | HTTP 429 Daily Quota Exceeded | `test_budget_and_usage.py` |
| **Per-Merchant Concurrency** | Max 10 concurrent inference jobs | Enqueue in priority queue | `test_budget_and_usage.py` |
| **Merchant Monthly Budget** | Configured per contract (e.g. $500/mo) | Block paid submissions; return size charts | `test_budget_and_usage.py` |
| **Global Emergency Switch** | `VTO_GLOBAL_KILL_SWITCH = true` | Fast-fail all new jobs; status retrieval stays open | `test_budget_and_usage.py` |

---

## 4. Usage Ledger & Reconciliation

The database table `tryon_usage_ledger` durably logs every invocation attempt:
- `job_id`: Internal job reference.
- `user_id`: Requesting shopper.
- `merchant_id`: Product merchant.
- `provider`: Provider identifier (e.g. `fashn`).
- `provider_request_id`: Upstream tracking ID.
- `is_cache_hit`: Boolean indicating if paid inference was bypassed.
- `estimated_cost_usd`: Estimated charge (e.g. `$0.05`).
- `reconciled_cost_usd`: Reconciled charge from monthly billing statement.
- `created_at`: Timestamp.

### Verification Results:
- 43 tests in `tests/unit/tryon/cache/run_all_cost_control_tests.py` passed (100%).
- Verified that cache hits generate zero provider egress and incur zero monetary charges.
- Verified that invalid hashes or non-positive quotas fail closed with descriptive domain errors.
