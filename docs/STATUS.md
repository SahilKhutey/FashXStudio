# FashXStudio: Honest Status
_Updated: 2026-11-11. Current stage: Pre-pilot engineering foundation and validation audit (Blueprint Phase 01–02). No real users, merchant partners, live vendors, or cloud production accounts exist yet. "Code" means written and tested in CI. In strict adherence to repository governance, a row may show ✅ ONLY with a link to an authentic human evidence card (docs/evidence/)._

Legend: 🟢 code and automated tests pass in CI · 🟡 partial · ⬜ not started · ❄️ frozen

| Area | Code & Automated CI Status | Real-World Evidence Status |
|:---|:---|:---|
| **Backend Platform** | 🟢 2,060 tests collected; 1,777 passed (non-frozen); 1,066 unit tests passed; Ruff passed; Mypy clean; Alembic head 0032 verified | None: Local PostgreSQL daemon unstarted (no Docker); verified in CI Postgres 16 container |
| **Authentication & Identity** | 🟢 LocalJWTVerifier with symmetric secret; default-deny middleware; RBAC | None: No external JWKS provider or Supabase auth tenant connected |
| **Persistence & Database** | 🟢 SQLAlchemy UOW, 32 linear Alembic revisions to head `0032_tryon_feedback_issue_tags` | None: Production cloud database unverified; local runs use CI container |
| **Virtual Try-On (VTO)** | 🟢 FASHN API adapter implemented; MockTryOnAdapter active default with preview watermark | None: No vendor account; no live commercial AI image generation ever executed |
| **Catalog & Ingestion** | 🟢 Multi-source pipeline, normalizer, dHash dedup, source registry | None: No live merchant feed; local CSV fixtures only; real VLM unmeasured |
| **Discovery & Personalization** | 🟢 Constrained MMR ranker, 11-feature scoring, fallback embeddings | None: Evaluated on synthetic test personas; zero human relevance ratings |
| **Mobile Application** | 🟢 22 Jest suites (165 tests); Expo Doctor 20/20 passed; Android Hermes bundle built | None: Simulator and test suite only; unverified on physical hardware |
| **Infrastructure & Deploy** | 🟢 GitHub Actions CI passing (6/6 jobs); S3/R2 storage adapter implemented | None: Storage defaults to `./.local_storage`; no production cloud environment |
| **Merchant Platform (B2B)** | 🟡 Code implemented; feature flag `ENABLE_B2B=False` (prohibited in prod for MVP) | None: Zero real merchants activated |
| **Operations & Experiments** | 🟡 Metrics contracts, deterministic experiment hashing, SLO schemas | None: No live production traffic |
| **Legal & Privacy** | 🟢 DPDP cascading erasure use cases, age gating (18+), consent tracking | None: Draft policies only; external counsel review unverified |
| **Closed Pilot Execution** | ⬜ Pilot measurement framework pre-registered; evaluators implemented | None: Quarantined simulated scenario only; real human pilot not run |
| **Commercial Validation** | ⬜ Business model hypothesis defined (ADR-0009 merchant handoff) | None: Zero revenue, zero merchant contracts |

## Pull request governance status
- **PR #33 (Recovery/rc13 final market readiness):** Merged into main. Governance evaluation framework consolidated; market release held.
- **PR #34 (Governance correction & metric reconciliation):** Open on branch `recovery/rc13.1-governance-correction`. CI workflow passed (6/6 jobs green). Includes Phase 02 audit consolidation, engineering standards (`docs/engineering/`), and baseline test reports. Human founder review and merge pending.
- **Engineering Standards:** Adopted in `docs/engineering/` with root PR template in `.github/PULL_REQUEST_TEMPLATE.md`.


## Release gates
Single source: [docs/release/gates.md](release/gates.md). All six release gates (G1–G6) remain **NOT MEASURED** and evaluated to **HOLD**. Gates cannot clear without authentic human evidence cards in `docs/evidence/`.

## Known technical debt
1. **Virtual Try-On Provider:** `TRYON_PROVIDER` defaults to `mock` (compositing with `PREVIEW ONLY - MOCK VTO` banner). Real FASHN API key not configured.
2. **Object Storage:** `STORAGE_BACKEND` defaults to `local` (`./.local_storage`). S3/Cloudflare R2 bucket unprovisioned.
3. **Catalog Feeds:** Relies on local seed fixtures (`curated-seed-catalog.csv`), quarantined from production discovery by ADR 0005. Live brand partner feeds pending.
4. **Local Postgres/Docker:** Local Windows environment lacks Docker/Postgres daemon; database integration tests run via CI service containers.
5. **Upstream Advisory:** `pip-audit` reports `PYSEC-2026-1845` against `pytest 8.4.2` (non-blocking in CI; tracked under Issue #21).
6. **Supabase Erasure Test:** 1 test xfailed (`tests/integration/test_erasure.py`) pending live Supabase auth project credentials.
