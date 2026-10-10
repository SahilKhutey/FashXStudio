# FashXStudio: Honest Status

_Last updated: 2026-10-10 · Source of truth for project status. Update in every phase PR._
_Baseline: [docs/logs/baseline-2026-10-04.md](logs/baseline-2026-10-04.md) · Phase 1: [docs/logs/task-log-phase01-restructure-honest-docs.md](logs/task-log-phase01-restructure-honest-docs.md) · Phase 3: [docs/logs/task-log-phase03-auth-and-security-spine.md](logs/task-log-phase03-auth-and-security-spine.md) · Phase 4: [docs/logs/task-log-phase04-real-persistence-and-storage.md](logs/task-log-phase04-real-persistence-and-storage.md) · Phase 5: [docs/logs/task-log-phase05-real-tryon-path.md](logs/task-log-phase05-real-tryon-path.md) · Phase 6: [docs/logs/task-log-phase06-real-catalog.md](logs/task-log-phase06-real-catalog.md) · [docs/logs/phase6-enrichment-2026-10-10.md](logs/phase6-enrichment-2026-10-10.md)_

**Measured:** tests [1,376 total: 1,130 MVP (not frozen) / 244 frozen] · ruff [856 errors in active tree] · mypy [0 issues in 802 files] · migrations [18, heads=1] · API routes [208 MVP / 235 with frozen]

Legend: ✅ real and tested · 🟡 partial/mocked · ⬜ not started · ❄️ frozen

## MVP scope
| Area | Status | Notes |
|---|---|---|
| Profile + photo quality gate | ✅ | Private S3/R2 object storage with signed capability URLs; pre-inference quality gate; EXIF strip & sanitization |
| Skin tone (Monk) calibration | 🟡 | Synthetic tests only |
| Consent + cascading erasure | 🟡 | Biometric and account erasure pipeline with Outbox StoragePurgeRequested and classification tests; needs legal review |
| Catalog ingest/dedup/normalization | ✅ | Direct brand feeds (FabIndia, Snitch, Westside) with partner agreements; Google Merchant CSV/XML parsers with defusedxml; SSRF defense; exact & dHash dedup; 1-command takedown CLI |
| VLM enrichment + embeddings | ✅ | GarmentAttrs schema with Anthropic VLM adapter & calibrated MockVlmClient; accuracy validated on 200-item gold standard (Category 100%, Color 96.5%, Sleeve 100%, Length 100%, Ethnic 100%); calibrated tau filters |
| 3-stage discovery feed | ✅ | Stage 1 discovery query strictly filters on cleared sources (CatalogSource.status == 'cleared') and active products; rights gating enforced |
| Try-on job lifecycle | ✅ | Two-phase submit/collect with FashnApiAdapter & MockAdapter; resumable worker, circuit breaker, per-user daily caps & budget ceiling |
| License-cleared try-on model | ✅ | FASHN Hosted API (tryon-v1.6 / Max) with commercial DPA & 72h auto-deletion; non-commercial models banned (Rule I08); capability gating for draped wear |
| GPU worker | ✅ | Resumable background worker with provider job recovery, C2PA synthetic watermarking, and private S3/R2 storage |
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
| G1 Functional | 🟡 | E2E on mocks and real FASHN adapter contracts passing |
| G2 ML quality | ✅ | **CLEARED:** 76.2% try-on acceptability on supported categories; VLM attribute extraction accuracy exceeds all pre-registered thresholds on 200-item gold standard |
| G3 Performance | 🟡 | Measured p95 vendor latency 11.4s, total queue+run p95 13.8s at concurrency 3 |
| G4 Privacy | 🟡 | Erasure pipeline implemented & tested on storage; Outbox pattern for asynchronous cleanup; table classification guard; needs legal review |
| G5 Commercial clearance | ✅ | Cleared via FASHN Hosted API (DPA executed, commercial terms verified, model license register in docs/architecture/model-licenses.md) |
| G6 User acceptance | ⬜ | No pilot |

## Known debt
- Import collision: RESOLVED in PR 2B. Unified into canonical package `backend/fashx/`. Both legacy roots `app/` and `api/app/` eliminated. Zero import collisions. PYTHONPATH hack eliminated.
- Duplicate mobile dirs: RESOLVED in PR 2C. Canonical app in `mobile/`, `apps/mobile` removed.
- Old docs quote different test/migration counts (663 vs 1271 tests; 12 vs 13 migrations); use the measured line above.
