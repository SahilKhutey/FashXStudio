# Phase 05.7 — Initial Catalog Targets Test Plan

## 1. Overview
This test plan provides comprehensive automated verification of the initial catalog targets, metric calculation engine, SSRF protections, and release gating logic established in Phase 05.7.

---

## 2. Test Matrix (CAT57-001 to CAT57-030)

| Test ID | Objective | Expected Outcome | Verification Status |
|:---|:---|:---|:---|
| **CAT57-001** | One approved live source with valid evidence and sync | Passes CAT-TGT-01 live feed metric | Automated (PASS) |
| **CAT57-002** | Source configured with mock adapter | Disqualified from live feed metric | Automated (PASS) |
| **CAT57-003** | Expired authorization reference | Fails compliance gate CAT-TGT-06 | Automated (PASS) |
| **CAT57-004** | Revoked source permission | Flags source as unauthorized active | Automated (PASS) |
| **CAT57-005** | 1,000 valid distinct merchant offers | Passes initial catalog size target CAT-TGT-02 | Automated (PASS) |
| **CAT57-006** | Feed rows with duplicate SKU/product IDs | Excludes duplicates from usable count | Automated (PASS) |
| **CAT57-007** | Offer with active quarantine record | Excluded from usable count | Automated (PASS) |
| **CAT57-008** | Inactive or out-of-lifecycle offer | Excluded from usable count | Automated (PASS) |
| **CAT57-009** | Product with missing/malformed URL | Excluded from usable count | Automated (PASS) |
| **CAT57-010** | Same canonical garment across 2 merchants | Counted as 1 garment, 2 merchant offers | Automated (PASS) |
| **CAT57-011** | Price verified within 24h window | Classified as FRESH | Automated (PASS) |
| **CAT57-012** | Price verified outside 24h window | Classified as STALE | Automated (PASS) |
| **CAT57-013** | Missing price verification timestamp | Classified as UNVERIFIED | Automated (PASS) |
| **CAT57-014** | Multi-currency catalog offers (INR, USD) | Retains distinct native currencies | Automated (PASS) |
| **CAT57-015** | Valid external merchant destination link | Classified as VALID (HTTP 200) | Automated (PASS) |
| **CAT57-016** | Destination link returning HTTP 404 | Classified as BROKEN | Automated (PASS) |
| **CAT57-017** | Transient HTTP 503 gateway error | Classified as TEMPORARY_FAILURE (not broken) | Automated (PASS) |
| **CAT57-018** | Destination resolving to private IP/loopback | Blocked by SSRF check (INVALID_REDIRECT) | Automated (PASS) |
| **CAT57-019** | HTTP 302 redirecting to internal IP | Blocked by SSRF redirect check | Automated (PASS) |
| **CAT57-020** | Image asset missing permission lineage | Fails traceability check (CAT-TGT-07) | Automated (PASS) |
| **CAT57-021** | Display permission granted without storage | Restricts storage operation | Automated (PASS) |
| **CAT57-022** | Image source missing VTO permission | Restricts virtual try-on processing | Automated (PASS) |
| **CAT57-023** | Image asset under deletion/takedown | Excluded from active asset accounting | Automated (PASS) |
| **CAT57-024** | Unauthorized active source connected | Fails overall compliance gate CAT-TGT-06 | Automated (PASS) |
| **CAT57-025** | Zero unauthorized active sources | Passes compliance gate CAT-TGT-06 | Automated (PASS) |
| **CAT57-026** | Repeated evaluation with frozen snapshot | Deterministic, identical results | Automated (PASS) |
| **CAT57-027** | Evaluation with missing or empty catalog | Reports incomplete measurement (HOLD) | Automated (PASS) |
| **CAT57-028** | Evaluation persistence and retrieval | Stored in `catalog_evaluation_runs` | Automated (PASS) |
| **CAT57-029** | Secret credential redaction in reports | No credentials leaked in metrics output | Automated (PASS) |
| **CAT57-030** | Historical evaluation run immutability | Runs are immutable once saved | Automated (PASS) |

---

## 3. Administrative API Verification

- `test_api_unauthorized_access_blocked`: Verifies 401/403 default-deny protection for unauthenticated or non-admin callers.
- `test_api_get_configured_targets`: Verifies retrieval of versioned pilot targets.
- `test_api_run_and_retrieve_evaluation`: Verifies triggering an on-demand evaluation run and fetching by UUID.
- `test_api_get_specific_views`: Verifies individual inspection endpoints for source health, quality breakdown, freshness, link health, and image compliance.
