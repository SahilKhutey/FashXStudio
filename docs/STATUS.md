# FashXStudio: Honest Status

_Last updated: 2026-10-08 · Source of truth for project status. Update in every phase PR._
_Baseline: [docs/logs/baseline-2026-10-04.md](logs/baseline-2026-10-04.md) · Phase 1 Log: [docs/logs/task-log-phase01-restructure-honest-docs.md](logs/task-log-phase01-restructure-honest-docs.md)_

**Measured:** tests [1,271 passed / 0 failed / 0 skipped] · ruff [856 errors in active tree] · mypy [0 issues in 802 files] · migrations [13, heads=1] · API routes [233]

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
| Authentication + ownership | ⬜ | routes with auth: 0 · routes with {user_id} in path: 20+ |
| Postgres persistence (MVP domains) | 🟡 | 16 in-memory repos wired at runtime (backend/fashx/repositories/*/memory.py) |
| Mobile app | ⬜ | Duplicate dirs: mobile/ (Expo 57, 229 files) vs apps/mobile (Expo 51, 9 files) |
| CI | ✅ | Canonical workflow (.github/workflows/ci.yml) with pgvector+redis active and verified green in PR 2A |

## Frozen (post-MVP; see docs/architecture/FROZEN.md)
Inventory (C05), promotions (C06), cart (C07), checkout/orders (C08), payments (C09), fulfilment (C10), returns (C11), regional (F12), engagement (F13).

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
- Duplicate mobile dirs (`mobile/` vs `apps/mobile`) - addressed in PR 2C.
- Old docs quote different test/migration counts (663 vs 1271 tests; 12 vs 13 migrations); use the measured line above.
