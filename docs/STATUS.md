# FashXStudio: Honest Status

_Last updated: 2026-10-09 · Source of truth for project status. Update in every phase PR._
_Baseline: [docs/logs/baseline-2026-10-04.md](logs/baseline-2026-10-04.md) · Phase 1 Log: [docs/logs/task-log-phase01-restructure-honest-docs.md](logs/task-log-phase01-restructure-honest-docs.md)_

**Measured:** tests [1,309 total: 1,065 MVP (not frozen) / 244 frozen] · ruff [856 errors in active tree] · mypy [0 issues in 802 files] · migrations [14, heads=1] · API routes [207 MVP / 234 with frozen]

Legend: ✅ real and tested · 🟡 partial/mocked · ⬜ not started · ❄️ frozen

## MVP scope
| Area | Status | Notes |
|---|---|---|
| Profile + photo quality gate | 🟡 | Logic/tests exist; no real image set or real storage yet |
| Skin tone (Monk) calibration | 🟡 | Synthetic tests only |
| Consent + cascading erasure | 🟡 | Implemented; needs legal review |
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
| Postgres persistence (MVP domains) | 🟡 | 16 in-memory repos wired at runtime (backend/fashx/repositories/*/memory.py) |
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
| G4 Privacy | 🟡 | Needs legal review + real-storage test |
| G5 Commercial clearance | ⬜ | No license-cleared try-on model |
| G6 User acceptance | ⬜ | No pilot |

## Known debt
- Import collision: RESOLVED in PR 2B. Unified into canonical package `backend/fashx/`. Both legacy roots `app/` and `api/app/` eliminated. Zero import collisions. PYTHONPATH hack eliminated.
- Duplicate mobile dirs: RESOLVED in PR 2C. Canonical app in `mobile/`, `apps/mobile` removed.
- Old docs quote different test/migration counts (663 vs 1271 tests; 12 vs 13 migrations); use the measured line above.
