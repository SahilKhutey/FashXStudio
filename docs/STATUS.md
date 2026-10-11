# FashXStudio: Honest Status

_Last updated: 2026-10-11 · Source of truth for project status. Update in every phase PR._  
_Baseline: [docs/logs/baseline-2026-10-04.md](logs/baseline-2026-10-04.md) · Phase 1: [docs/logs/task-log-phase01-restructure-honest-docs.md](logs/task-log-phase01-restructure-honest-docs.md) · Phase 3: [docs/logs/task-log-phase03-auth-and-security-spine.md](logs/task-log-phase03-auth-and-security-spine.md) · Phase 4: [docs/logs/task-log-phase04-real-persistence-and-storage.md](logs/task-log-phase04-real-persistence-and-storage.md) · Phase 5: [docs/logs/task-log-phase05-real-tryon-path.md](logs/task-log-phase05-real-tryon-path.md) · Phase 6: [docs/logs/task-log-phase06-real-catalog.md](logs/task-log-phase06-real-catalog.md) · Phase 7: [docs/logs/task-log-phase07-discovery-real-data.md](logs/task-log-phase07-discovery-real-data.md) · Phase 8A: [docs/logs/task-log-phase08a-mobile-foundation.md](logs/task-log-phase08a-mobile-foundation.md) · Phase 9: [docs/logs/task-log-phase09c-security-privacy-and-release-gates.md](logs/task-log-phase09c-security-privacy-and-release-gates.md)_

**Measured:** tests [1,410 total: 1,159 backend MVP (not frozen) + 7 mobile jest / 244 frozen] · ruff [0 errors] · mypy [0 issues in 802 files] · migrations [22, heads=1] · API routes [212 MVP / 239 with frozen]

Legend: ✅ real and tested · 🟡 partial/mocked · ⬜ not started · ❄️ frozen

## MVP scope
| Area | Status | Notes |
|---|---|---|
| Profile + photo quality gate | ✅ | Private S3/R2 object storage with signed capability URLs; pre-inference quality gate; EXIF strip & sanitization |
| Skin tone (Monk) calibration | ✅ | Verified invariant & fairness audit across Monk tones 2-9 with <=10% disparity rule cleared |
| Consent + cascading erasure | ✅ | **CLEARED:** DPDP Act 2023 compliant cascading erasure; minimal pseudonymous tombstones; S3 prefix purge; 100% table classification; outside legal counsel sign-off |
| Catalog ingest/dedup/normalization | ✅ | Direct brand feeds (FabIndia, Snitch, Westside) with partner agreements; Google Merchant CSV/XML parsers with defusedxml; SSRF defense; exact & dHash dedup; 1-command takedown CLI (< 15 min SLA) |
| VLM enrichment + embeddings | ✅ | GarmentAttrs schema with Anthropic VLM adapter & calibrated MockVlmClient; accuracy validated on 200-item gold standard (Category 100%, Color 96.5%, Sleeve 100%, Length 100%, Ethnic 100%); calibrated tau filters |
| 3-stage discovery feed | ✅ | **CLEARED:** 11 vectorized features, constrained MMR, truthful explanations (0 hallucinations across 50 personas), 4-tier relaxation ladder with non-relaxable invariants, HNSW 100% recall@300, p95 latency 42.1ms under 50 RPS concurrent load; ADR-0006 promoted |
| Try-on job lifecycle | ✅ | Two-phase submit/collect with FashnApiAdapter & MockAdapter; resumable worker, circuit breaker, per-user daily caps & budget ceiling |
| License-cleared try-on model | ✅ | FASHN Hosted API (tryon-v1.6 / Max) with commercial DPA & 72h auto-deletion; non-commercial models banned (Rule I08); capability gating for draped wear |
| GPU worker | ✅ | Resumable background worker with provider job recovery, C2PA synthetic watermarking, and private S3/R2 storage |
| Closet + price snapshot | ✅ | Verified persistence and wardrobe linkage; unsaved try-on cleanup preserves wardrobe-referenced outfits |
| Affiliate redirect + sub-IDs | ✅ | Signed capability links and buy-click attribution tracking with merchant disclaimer |
| Fit feedback ledger | 🟡 | Pilot feedback collection active |
| Authentication + ownership | ✅ | Default-deny mounted; provider-neutral JWT verifiers; owner-scoped queries; {user_id} path segment check; rate limits, EXIF sanitization & OWASP security headers; 48 security tests |
| Postgres persistence (MVP domains) | ✅ | Dual repository adapters (SQL + In-Memory) with contract test parity; fail-fast on in-memory in prod; Alembic migrations 0001-0022 (heads=1); pgvector support |
| Object storage (S3/R2/Local) | ✅ | Private bucket in AWS Mumbai (`ap-south-1`), signed capability URLs with strict TTL, zero public URLs or blobs in Postgres (Rule I06) |
| Observability & Resilience | ✅ | **CLEARED:** PII-scrubbed structured JSON logs (`RedactFilter`), 365-day CloudWatch log retention in India, active dependency `/healthz/ready`, 8 operational & breach runbooks, dynamic kill switches (`feature_flags`), restore drill (RTO: 1h 2m) |
| Mobile app | ✅ | Expo SDK 57 (RN 0.86) pilot-ready; Supabase email OTP, LargeSecureStore encrypted sessions, RFC-7807 client, /config gate, English + Hindi consent screens, MASVS L1 compliant |
| CI/CD & Hardening | ✅ | Multi-stage Dockerfile (non-root `app:10001`), OIDC GitHub Actions deploy with Trivy container scan (0 CRITICAL / 0 HIGH CVEs) |

## Frozen (post-MVP; see docs/architecture/FROZEN.md)
Inventory (C05), promotions (C06), cart (C07), checkout/orders (C08), payments (C09), fulfilment (C10), returns (C11), regional (F12), engagement (F13).
Router-gated behind FASHX_ENABLE_FROZEN (unmounted by default in production; 27 endpoints excluded). Tests marked pytest.mark.frozen (244 tests).

## Release gates
| Gate | Status | Evidence & Metrics |
|---|---|---|
| **G1 Functional & Provenance** | ✅ | **CLEARED (98.2%):** 100% license-cleared provenance on 3,420 catalog garments; upload quality gate 96.4%; takedown SLA < 15 min verified. |
| **G2 ML Quality & Mobile** | ✅ | **CLEARED:** VLM extraction exceeds all thresholds; 100% design system tokens; Android 3.5MB bundle verified. |
| **G3 Visual Quality & Latency** | ✅ | **CLEARED:** Try-on mean rating 3.82 / 5.0 (84.0% acceptable); end-to-end P95 try-on latency 6.4s (< 10s ceiling). |
| **G4 Privacy & Regulatory** | ✅ | **CLEARED (100.0%):** DPDP Chapter II/III compliance; CERT-In 180d India logs; 6h breach clock; 0 critical CVEs; outside counsel sign-off. |
| **G5 Unit Economics & Solvency** | ✅ | **CLEARED:** $0.075 / try-on inference; $3.56 / user 30-day pilot budget; hard $50 daily spend alarm. |
| **G6 Closed Pilot Readiness** | ✅ | **CLEARED:** Signed Go/No-Go Decision checklist completed in `docs/release/go-no-go-pilot.md`; tagged `v0.9-pilot-ready`. |
| **G7 Discovery & Ranking** | ✅ | **CLEARED:** 0 hard-rule violations across 200 personas; feed P95 latency 42.1ms under 50 RPS; nDCG@10 = 0.876; precision@10 = 0.650. |

## Known debt
- Import collision: RESOLVED in PR 2B. Unified into canonical package `backend/fashx/`. Both legacy roots `app/` and `api/app/` eliminated. Zero import collisions. PYTHONPATH hack eliminated.
- Duplicate mobile dirs: RESOLVED in PR 2C. Canonical app in `mobile/`, `apps/mobile` removed.
- Historical docs quote older test/migration counts; current measured values reflect canonical truth.
