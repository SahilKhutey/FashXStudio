# Phase 05.1 Acceptance Report: Merchant and Source Authorization

**Workstream**: Phase 05 — Workstream 5.1 (P0 Foundation)  
**Deliverable**: Merchant and Source Authorization Subsystem  
**Date**: November 2026  
**Status**: 🟢 Code Complete & CI Gate Passed

---

## 1. Executive Summary
Workstream 5.1 establishes the permission-aware merchant and source registry for FashXStudio before connecting live product catalogs. It guarantees that no catalog source is permitted to publish products, store media, process images with AI, or redirect shoppers without verified merchant identity, validated contractual evidence, and granular permission grants.

---

## 2. Delivered Capabilities & Deliverables

### 2.1 Database Models & Migrations
- Migration: `database/migrations/versions/0038_add_catalog_authorization_and_sources.py`
- Extensions:
  - `merchants`: Added `legal_name`, `display_name`, `website`, `country_code`, `registration_reference`, `verification_status`, contact UUIDs.
  - `catalog_sources`: Added `merchant_id`, `source_name`, `source_type`, `source_owner`, `provider_name`, `access_method`, `credential_secret_ref`, `source_status`, `market_codes`, `category_codes`, review/expiry timestamps.
- New Tables:
  - `catalog_authorization_evidence`: Verified document references, SHA-256 hashes, signatory roles, verification status.
  - `catalog_source_permissions`: Append-only granular permission records with category, market, and processor restrictions.
  - `catalog_takedown_requests`: Formal audit records of takedowns, reason codes, status, and resolution notes.
  - `catalog_authorization_decisions`: Immutable audit event log for every engine decision.

### 2.2 Backend Domain Architecture
- `backend/fashx/catalog/merchants/`: Merchant schemas, repository, and service enforcing unique legal names, registration references, and status transitions.
- `backend/fashx/catalog/sources/`: Source schemas, repository, lifecycle state machine, and service.
- `backend/fashx/catalog/authorization/`: 11-step fail-closed `CatalogAuthorizationEvaluator`, authorization service, and `CatalogExpiryWorker`.
- `backend/fashx/catalog/takedowns/`: Takedown repository, immediate suspension service, and `TakedownAsyncWorker`.
- `backend/fashx/catalog/ingestion/`: `CatalogAuthorizationGuard` enforcing fail-closed checks across pipeline stages.
- `backend/fashx/catalog/adapters/`: Base permission-aware adapter contract and concrete adapters for Merchant API, Affiliate API, Feed, and Partner Export.
- `backend/fashx/catalog/admin_router.py`: 14 administrative endpoints mounted at `/api/v1/admin/catalog`.

---

## 3. Automated Test Verification Summary

The test suite covers all required operational scenarios:

### Test Suites:
1. `tests/catalog/test_merchants_and_sources.py`: 10 passed (CAT-AUTH-001 through CAT-AUTH-010).
2. `tests/catalog/test_permissions_and_evaluator.py`: 18 passed (CAT-PERM-001 through CAT-PERM-018).
3. `tests/catalog/test_takedowns.py`: 10 passed (CAT-TAKE-001 through CAT-TAKE-010).
4. `tests/catalog/test_authorization_integration.py`: 1 passed (19-step end-to-end integration scenario).
5. `tests/catalog/test_manage_catalog_source.py`: 10 passed (legacy regression suite).
6. `tests/catalog/test_product_feed.py`: 15 passed (legacy regression suite).

**Total Catalog Tests**: 64 passed in 14.95s.  
**OpenAPI Route Snapshot**: 2 passed in 4.97s (273 verified routes).  
**Code Quality**: Ruff check clean, Ruff format clean, Docs lint clean.
