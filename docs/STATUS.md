# FashXStudio: Honest Status

_Last updated: 2026-10-09 · Source of truth for project status. Update in every phase PR._
_Baseline: [docs/logs/baseline-2026-10-04.md](logs/baseline-2026-10-04.md) · Phase 1 Log: [docs/logs/task-log-phase01-restructure-honest-docs.md](logs/task-log-phase01-restructure-honest-docs.md)_

**Measured:** tests [1,334 total: 1,090 MVP (not frozen) / 244 frozen] · ruff [856 errors in active tree] · mypy [0 issues in 802 files] · migrations [16, heads=1] · API routes [208 MVP / 235 with frozen]

Legend: ✅ real and tested · 🟡 partial/mocked · ⬜ not started · ❄️ frozen

## MVP scope
| Area | Status | Notes |
|---|---|---|
| Profile + photo quality gate | ✅ | Private S3/R2 object storage with signed capability URLs; pre-inference quality gate; EXIF strip & sanitization |
| Skin tone (Monk) calibration | 🟡 | Synthetic tests only |
| Consent + cascading erasure | 🟡 | Biometric and account erasure pipeline with Outbox StoragePurgeRequested and classification tests; needs legal review |
| Catalog ingest/dedup/normalization | 🟡 | No legitimate live source connected |
| VLM enrichment + embeddings | 🟡 | Accuracy unmeasured |
| 3-stage discovery feed | 🟡 | Test data only |
| Try-on job lifecycle | 🟡 | Runs on MockAdapter |
| License-cleared try-on model | ⬜ | Blocker (rule I08 / gate G5) |
| GPU worker | ⬜ | Contracts only |
| Closet + price snapshot | 🟡 | Verify persistence |
| Affiliate redirect + sub-IDs | 🟡 | No live affiliate program |
| Fit feedback ledger | 🟡 | Cold-start: needs real outcomes |
| Authentication + ownership | ✅ | Default-deny mounted; provider-neutral JWT verifiers; owner-scoped queries; {user_id} path segment check; rate limits, EXIF sanitization & OWASP security headers; 38 security tests |
| Postgres persistence (MVP domains) | ✅ | Dual repository adapters (SQL + In-Memory) with contract test parity (8 contract suites, 32 tests passing on both); fail-fast on in-memory in prod; Alembic migrations 0001-0016; pgvector support |
| Object storage (S3/R2/Local) | ✅ | Private bucket, signed capability URLs with strict TTL (300s), zero public URLs or blobs in Postgres (Rule I06), contract tests against local & Moto S3 |
| Mobile app | 🟡 | Canonical Expo 57 app consolidated in mobile/ (229 files); apps/mobile deleted (PR 2C); mobile typecheck tracked in CI |
| CI | ✅ | Canonical workflow with required backend (pgvector+redis), non-blocking frozen job, and mobile job (PR 2A/2C) |

## Frozen (post-MVP; see docs/architecture/FROZEN.md)
Inventory (C05), promotions (C06), cart (C07), checkout/orders (C08), payments (C09), fulfilment (C10), returns (C11), regional (F12), engagement (F13).
Router-gated behind FASHX_ENABLE_FROZEN (unmounted by default in production; 27 endpoints excluded). Tests marked pytest.mark.frozen (244 tests).

## Release gates
| Gate | Status | Blocker |
|---|---|---|
| G1 Functional | 🟡 | E2E on mocks only (SQLite in-memory test runner) |
| G2 ML quality | ⬜ | Needs real models + labeled sample |
| G3 Performance | ⬜ | Needs real GPU + load test |
| G4 Privacy | 🟡 | Erasure pipeline implemented & tested on storage; Outbox pattern for asynchronous cleanup; table classification guard; needs legal review |
| G5 Commercial clearance | ⬜ | No license-cleared try-on model |
| G6 User acceptance | ⬜ | No pilot |

## Known debt
- Import collision: RESOLVED in PR 2B. Unified into canonical package `backend/fashx/`. Both legacy roots `app/` and `api/app/` eliminated. Zero import collisions. PYTHONPATH hack eliminated.
- Duplicate mobile dirs: RESOLVED in PR 2C. Canonical app in `mobile/`, `apps/mobile` removed.
- Old docs quote different test/migration counts (663 vs 1271 tests; 12 vs 13 migrations); use the measured line above.
