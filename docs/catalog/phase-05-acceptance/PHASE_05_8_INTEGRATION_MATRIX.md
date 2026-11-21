# Phase 05.8: Deliverables and Integration Matrix

## 1. Overview

This matrix tracks the operational status, automated verification, code components, and governance boundaries for each of the nine deliverables established in Phase 05 (Automated Catalog Acquisition and Merchant Integrations).

Per repository rules:
- **`LOCAL_VERIFIED`**: Automated test suite passed on the local development engine (SQLite async engine via aiosqlite).
- **`CI_VERIFIED`**: Automated tests validated against PostgreSQL 16 container in GitHub Actions.
- **`NOT_MEASURED_IN_PROD`**: Real-world cloud production or commercial merchant integration has not been executed; awaiting founder evidence cards in `docs/evidence/`.

---

## 2. Deliverables Integration Matrix

| ID | Deliverable | Primary Modules | Current Status | Verification Target | Test Cases | Governance Constraint |
|:---|:---|:---|:---|:---|:---|:---|
| **DEL-01** | **Merchant Onboarding & Auth Records** | `fashx.catalog.permissions`, `database.models.catalog_auth` | `LOCAL_VERIFIED` / `CI_VERIFIED` | Merchant identity, legal agreement references, permission history | `P58-001`, `P58-002`, `P58-020` | No live partner contracts; synthetic test fixtures only |
| **DEL-02** | **Source Registry** | `CatalogSource`, `SourceLifecycleService` | `LOCAL_VERIFIED` / `CI_VERIFIED` | Source status, adapters, scopes, lifecycle transitions | `P58-002`, `P58-003` | Admin role required for operational status change |
| **DEL-03** | **Live Connector Framework** | `fashx.catalog.acquisition.connectors`, `retry_transient` | `LOCAL_VERIFIED` / `CI_VERIFIED` | HTTP CSV/JSON streaming, bounded retry, cursor pagination | `P58-003`, `P58-004`, `P58-017` | SSRF private IP blocked; test HTTP fixtures used |
| **DEL-04** | **Catalog Ingestion Pipeline** | `AcquisitionPipeline`, `IngestionNormalizer` | `LOCAL_VERIFIED` / `CI_VERIFIED` | Field validation, quarantine, idempotent deduplication | `P58-005`, `P58-006`, `P58-007`, `P58-008` | Zero prices or invalid categories quarantined |
| **DEL-05** | **Canonical Catalog Database** | `database.models.catalog`, `CatalogUnitOfWork` | `LOCAL_VERIFIED` / `CI_VERIFIED` | Canonical garment resolution, multi-merchant offers | `P58-009`, `P58-013`, `P58-014` | Postgres migrations 0038–0044; schema checked |
| **DEL-06** | **Product Image Pipeline** | `CatalogImageAsset`, `CatalogImageService`, `fashx.catalog.images` | `LOCAL_VERIFIED` / `CI_VERIFIED` | Storage permissions, dHash dedup, VTO isolation, purge | `P58-010`, `P58-011`, `P58-012`, `P58-022` | Local storage mock; no live external S3 bucket |
| **DEL-07** | **Merchant Catalog Operations** | `MerchantProductUpdateService`, `SourceTakedownService` | `LOCAL_VERIFIED` / `CI_VERIFIED` | Tenant isolation, takedown execution, product overrides | `P58-019`, `P58-021`, `P58-025`, `P58-026` | Merchants restricted strictly to own merchant_id |
| **DEL-08** | **Freshness & Reconciliation** | `CatalogFreshnessService`, `CatalogReconciliationService` | `LOCAL_VERIFIED` / `CI_VERIFIED` | Price history audit, incomplete snapshot guard, safe sync | `P58-015`, `P58-016`, `P58-018`, `P58-027` | Partial sync does not mass-deactivate active items |
| **DEL-09** | **Catalog Targets Framework** | `CatalogEvaluationService`, `LinkHealthEvaluator` | `LOCAL_VERIFIED` / `CI_VERIFIED` | Metrics evaluation, link health sampling, exit gate rules | `CAT-TGT-01` to `CAT-TGT-09` | Founder evidence required for real-world pilot clearance |

---

## 3. Subsystem Integration Verification Summary

All 9 deliverables have functional code implementations and corresponding automated unit and integration tests:
- Total Phase 05.8 integration test cases: **28 / 28 passing**
- Coverage span: Merchant onboarding, source authorization, connector retry, pipeline ingestion, data normalization, deduplication, multi-offer preservation, image rights, display derivation, VTO gating, customer shopping API, price & availability drift, partial sync resilience, takedowns, cache invalidation, post-takedown sync safety, tenant isolation, durable crash recovery, and full-lifecycle audit logging.
