# 13 — Test Catalogue

## 1. Test Suite Coverage

The Phase 08.1 test catalogue validates every architectural component, invariant, and failure mode.

| Test ID | Area | Verification Target |
|---|---|---|
| `SZ-SCH-001` | Schemas | Validate valid `SizeChartRevisionCreate` models with valid units and fields |
| `SZ-SCH-002` | Schemas | Reject payload with duplicate size labels in same chart |
| `SZ-SCH-003` | Schemas | Reject payload with duplicate measurement fields in same row |
| `SZ-SCH-004` | Schemas | Enforce strictly positive measurement values |
| `SZ-SYS-001` | Sizing Systems | Verify standard system registration (US, UK, EU, INTL, WAIST, COLLAR) |
| `SZ-SYS-002` | Sizing Systems | Refuse unverified conversion between arbitrary sizing systems |
| `SZ-SYS-003` | Sizing Systems | Verify label normalization (trimming, casing, hyphens) |
| `SZ-FLD-001` | Field Definitions | Verify field registry definitions and category eligibility |
| `SZ-FLD-002` | Field Definitions | Verify physical range limits for standard fields |
| `SZ-UNT-001` | Unit Normalization | Deterministic conversion from INCH to CM with 2.54 factor |
| `SZ-UNT-002` | Unit Normalization | Round Half-Up precision quantization to 0.01 |
| `SZ-UNT-003` | Unit Normalization | Reject negative, zero, infinite, and NaN inputs |
| `SZ-VAL-001` | Validation Service | Reject unknown measurement field codes |
| `SZ-VAL-002` | Validation Service | Reject measurements violating category compatibility |
| `SZ-VAL-003` | Validation Service | Reject measurements outside min/max range limits |
| `SZ-VAL-004` | Validation Service | Generate warning on non-monotonic size progression |
| `SZ-FPT-001` | Fingerprinting | Canonical fingerprinting excludes volatile timestamps |
| `SZ-FPT-002` | Fingerprinting | Identical payloads with different row order produce same fingerprint |
| `SZ-FRE-001` | Freshness | Size chart active within 90 days is marked fresh |
| `SZ-FRE-002` | Freshness | Size chart older than 90 days is marked stale |
| `SZ-FRE-003` | Freshness | Inventory older than 24 hours degrades from IN_STOCK to UNKNOWN |
| `SZ-FRE-004` | Freshness | Inventory staleness never falsifies OUT_OF_STOCK |
| `SZ-AVL-001` | Availability | Ingest inventory snapshot and report current stock |
| `SZ-REP-001` | Repository | Create product size chart container and persist revision |
| `SZ-REP-002` | Repository | Increment version and deactivate previous current revision |
| `SZ-REP-003` | Repository | Quarantine invalid submission with error codes |
| `SZ-SRV-001` | Service | End-to-end ingestion creates v1 revision |
| `SZ-SRV-002` | Service | Identical ingestion creates NO_OP_UNCHANGED event without version bump |
| `SZ-SRV-003` | Service | Ingestion with changed dimensions creates v2 revision |
| `SZ-API-001` | REST API | GET /products/{id}/size-chart returns active chart |
| `SZ-API-002` | REST API | GET /products/{id}/size-chart returns 200 UNAVAILABLE when missing |
| `SZ-API-003` | REST API | GET /products/{id}/size-chart returns 404 for non-existent product |
| `SZ-API-004` | REST API | POST /products/{id}/size-chart ingests and returns 201 |
| `SZ-API-005` | REST API | POST /products/{id}/size-chart rejects invalid payload with 422 |
| `SZ-E2E-001` | End-to-End | Backward compatibility with Phase 07.8 size chart methods |
