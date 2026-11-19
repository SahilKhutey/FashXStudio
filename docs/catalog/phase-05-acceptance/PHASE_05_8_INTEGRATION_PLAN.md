# Phase 05.8: End-to-End Catalog Lifecycle Integration Plan

## 1. Executive Summary & Objective

Phase 05.8 establishes the integration and acceptance framework that unifies all catalog acquisition, authorization, processing, and management subsystems delivered in Phases 05.1 through 05.7 into a single cohesive, permission-aware catalog operating lifecycle.

The central invariant governing this architecture is:
> **No product data, image asset, or merchant offer may enter, exist within, or be served by the FashXStudio catalog without verifiable source authorization, active permission scopes, and end-to-end lifecycle control.**

This plan details the subsystem topology, data flow contracts, and verification checkpoints that bind Phases 05.1–05.7 into a unified system ready for pilot operation.

---

## 2. Integrated Subsystem Topology

The FashXStudio catalog operating system connects seven specialized subsystems:

```
[ Phase 05.1: Merchant & Source Authorization ]
  │
  ├─► Source Registry & Credentials
  ├─► Permission Scopes (READ, STORE, IMAGE, VTO)
  └─► Evidence Records & Expiry
        │
        ▼
[ Phase 05.2: Source Adapter Layer ]
  │
  ├─► Secure Connectors (HTTP CSV, JSON, API)
  ├─► SSRF-Protected Fetch & Bounded Retries
  └─► Checkpointed Sync & Pagination
        │
        ▼
[ Phase 05.3: Canonical Ingestion Pipeline ]
  │
  ├─► Permission Pre-Flight Verification
  ├─► Field Validation & Sanitization
  ├─► Category Normalization & Quarantine
  └─► Content Hashing & Idempotent Upsert
        │
        ├────────────────────────────────┐
        ▼                                ▼
[ Phase 05.4: Image Pipeline ]   [ Phase 05.5: Catalog Database & Freshness ]
  │                                │
  ├─► Storage Permission Check     ├─► Canonical Garments & Multi-Merchant Offers
  ├─► Byte / Dimension Validation  ├─► Immutable Offer Price History
  ├─► dHash Deduplication         ├─► Reconciliation & Stale Drift Detection
  └─► Private Derivative Store     └─► Provenance Graph & Snapshot Audit
        │                                │
        └─────────────────┬──────────────┘
                          │
                          ▼
[ Phase 05.6: Merchant Operations & Control Plane ]
  │
  ├─► Admin Source Controls & Takedown Execution
  ├─► Merchant Self-Service Offer Management
  ├─► Product Field Overrides & Quarantine Remediation
  └─► Tenant Isolation Enforcement
        │
        ▼
[ Phase 05.7: Targets, Link Health & Exit Gate ]
  │
  ├─► 1,000 Usable Products Quality Framework
  ├─► Link Health & Redirect Validation
  ├─► Shopper-Facing Discovery Gate (Active & Non-Takedown)
  └─► Automated Evaluation & Gate Verification
```

---

## 3. Subsystem Hand-Off Contracts

### 3.1 Authorization to Ingestion Hand-Off (05.1 ➔ 05.3)
- Ingestion runs check `CatalogSource.source_status == "ACTIVE"`, `CatalogSource.is_enabled == True`, and `CatalogSourcePermission` records for `PRODUCT_DATA_READ` and `PRODUCT_DATA_STORE`.
- If authorization expires or is revoked, the pipeline halts with `CatalogAuthorizationError`.

### 3.2 Adapter to Ingestion Hand-Off (05.2 ➔ 05.3)
- Source adapters yield `AcquisitionBatch` records containing validated `SourceProduct` objects.
- Ingestion pipeline tracks cursor checkpoints in `CatalogSyncCheckpoint`, enabling durable resume after worker restart or transient network failure.

### 3.3 Ingestion to Image Pipeline Hand-Off (05.3 ➔ 05.4)
- Product image references are processed only if `IMAGE_STORE` and `IMAGE_DISPLAY` permissions are granted.
- If `VTO_PROCESS` permission is absent, images are restricted to display derivatives; AI garment segmentation and VTO pipelines are strictly prohibited from consuming the asset.

### 3.4 Ingestion to Catalog Database Hand-Off (05.3 ➔ 05.5)
- Canonical garments are resolved or created; merchant offers are bound via `(merchant_id, source_product_id)`.
- If two merchants provide the same garment, separate offers are maintained, ensuring fair merchant competition and accurate attribution.
- Price observations generate immutable `OfferPriceHistory` records.

### 3.5 Operations to Shopper Hand-Off (05.6 ➔ 05.5 / Shopper API)
- Merchant takedowns or administrative freezes flag records with `takedown_status = COMPLETED` and `status = INACTIVE`.
- The customer garment router (`_resolve_garment_detail`) filters out any offer under takedown or non-active status.
- If all merchant offers for a garment are removed, the customer API responds with HTTP 404 (`EntityNotFoundError`), preventing shopper discovery of unavailable items.

---

## 4. Verification Checkpoints

| Checkpoint | Target Phase | Subsystems Involved | Verified In Test Suite |
|:---|:---|:---|:---|
| **CP-01: Onboarding** | 05.1 | Authorization Registry | `test_p58_001_verify_merchant_onboarding` |
| **CP-02: Auth Enforcement** | 05.1, 05.6 | Registry, Lifecycle Service | `test_p58_002_connect_unauthorized_source_activation_blocked` |
| **CP-03: Live Connector** | 05.2 | Source Adapters, Registry | `test_p58_003_connect_approved_live_source_verified` |
| **CP-04: Idempotent Ingest** | 05.3 | Ingestion Pipeline, UOW | `test_p58_008_ingest_duplicate_source_record_idempotent` |
| **CP-05: Multi-Merchant** | 05.5 | Canonical Garments, Offers | `test_p58_009_same_garment_from_another_merchant_separate_offers` |
| **CP-06: Image Compliance** | 05.4 | Image Pipeline, Permissions | `test_p58_010`, `test_p58_011`, `test_p58_012` |
| **CP-07: Shopper Discovery** | 05.5, API | Customer Router, API | `test_p58_013`, `test_p58_014` |
| **CP-08: Takedown Response** | 05.6, API | Takedown Service, Router | `test_p58_021`, `test_p58_024`, `test_p58_025` |
| **CP-09: Tenant Isolation** | 05.6 | Product Services, UOW | `test_p58_026_merchant_tenant_isolation` |
| **CP-10: Audit Trail** | 05.1, 05.6 | Audit Service, DB | `test_p58_028_full_lifecycle_audit` |

---

## 5. Exit Criteria for Acceptance
Acceptance of Phase 05.8 requires:
1. All 28 automated integration tests (`P58-001` through `P58-028`) pass without failures.
2. Complete documentation matrix covering integration plan, acceptance report, security validation, and test executions.
3. No regressions in route snapshots or shopper customer APIs.
4. Adherence to repo rules: no simulated evidence claims; local runs on SQLite, Postgres verified in CI.
