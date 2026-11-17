# FashXStudio — Phase 01.5 Analytics & Telemetry Automated Test Plan

**Document ID:** `FASHX-TEST-002`  
**Version:** `1.0 — Execution Baseline`  
**Date:** `10 November 2026`  
**Scope:** `Phase 01.5 — Verification & Automated Test Specifications`  

---

## 1. Test Strategy & Scope

The analytics testing harness verifies four critical requirements:
1. **Schema & PII Integrity:** 100% of emitted events strictly conform to JSON schemas and exclude biometric/PII data.
2. **Transactional Event Guarantee:** Events are emitted if and only if database transactions successfully commit.
3. **Calculation Math Correctness:** SQL queries and aggregation workers handle boundary conditions (zero division, single retries, duplicate clicks) accurately.
4. **Tenant Isolation:** Merchant reporting queries strictly filter events by `merchant_id`.

---

## 2. Automated Test Case Inventory

| Test ID | Test Category | Target File / Class | Scenario & Assertion |
| :--- | :--- | :--- | :--- |
| **ANL-001** | Schema Validation | `test_analytics_event_schemas.py` | Universal event envelope validates valid UUIDs, timestamps, and known event names. |
| **ANL-002** | PII Leak Prevention | `test_analytics_event_schemas.py` | Asserts regex patterns reject raw email addresses, phone numbers, and full names in `properties`. |
| **ANL-003** | Image Exclusion Guard | `test_analytics_event_schemas.py` | Asserts `properties` rejects raw image binary bytes or presigned S3 URLs. |
| **ANL-004** | Transactional Outbox | `test_event_emission.py` | Transaction rollback (simulated exception) results in zero emitted analytics events. |
| **ANL-005** | Post-Commit Dispatch | `test_event_emission.py` | Successful commit pushes formatted event to Redis stream `stream:fashx:analytics`. |
| **ANL-006** | Zero-Division Guard | `test_kpi_aggregation_math.py` | Asserts all 14 KPI SQL queries return `NULL` or `0.0` when denominators are zero. |
| **ANL-007** | First-Attempt Math | `test_kpi_aggregation_math.py` | Correctly segregates `attempt_count = 1` from total eventual completions. |
| **ANL-008** | Distinct Shopper CTR | `test_kpi_aggregation_math.py` | Multiple clicks on the same product within one session increment click count once for unique CTR. |
| **ANL-009** | Tenant Isolation | `test_merchant_analytics.py` | Merchant A calling `GET /api/v1/merchants/{b}/analytics` receives `HTTP 403 FORBIDDEN`. |
| **ANL-010** | D7 Retention Math | `test_kpi_aggregation_math.py` | Cohort active on Day 8 post-signup is counted in D7 window; Day 15 activity excluded. |
| **ANL-011** | Idempotent Job Dedupe | `test_vto_metrics_pipeline.py`| Submissions sharing `idempotency_key` create exactly one `vto_jobs` row and one `vto_started` event. |
| **ANL-012** | CSV Export Delivery | `test_analytics_exports.py` | `POST /analytics/exports` yields valid downloadable CSV matching database aggregates. |
