# FashXStudio — Engineering Gaps, Mock Audits & Technical Debt

**Document ID:** `FASHX-GAP-001`  
**Phase:** `Phase 02 — Repository Audit and Engineering Consolidation`  
**Section:** `2.2 — Engineering Gaps & Risk Analysis`  
**Date:** `11 November 2026`  
**Status:** `AUDIT RECORDED — REMEDIATION PLANNED`  

---

## 1. Executive Summary

The Phase 02.2 repository audit confirmed that FashXStudio possesses a mature, tested core application architecture with clean separation of concerns, 32 linear database migrations, 222 API endpoints, and a comprehensive mobile application.

However, the audit identified **five technical gaps, incomplete modules, or mocked integrations** that must be recognized and addressed before commercial launch:

| Gap ID | Subsystem | Classification | Severity | Impact on Pilot MVP v1.0 |
| :--- | :--- | :---: | :---: | :--- |
| **GAP-01** | Merchant B2B Portal & Dashboard | **Mock / Inactive** | Medium | Low (B2B self-serve portal deferred; Admin API handles pilot) |
| **GAP-02** | Root Pytest Fixture Autouse Debt | **Partial / Defect** | Medium | High for local developer DX; Zero for CI |
| **GAP-03** | Live VTO Provider Execution in CI | **Mock Default** | High | Expected for CI cost control; requires staging verification |
| **GAP-04** | FashionCLIP Embedding Inference | **Mock Fallback** | Medium | Pre-computed embeddings suffice for pilot catalog |
| **GAP-05** | Legacy Remote Feature Branches | **Unpruned Debt** | Low | Requires branch audit and cleanup |

---

## 2. In-Depth Technical Gap Analysis

### GAP-01: Merchant Dashboard Hardcoded Mock Metrics
- **Location:** [`backend/fashx/b2b/dashboard.py#L22-L58`](file:///c:/Users/ASUS/Documents/FashXStudio/backend/fashx/b2b/dashboard.py#L22-L58)
- **Code Observation:**
  ```python
  @router.get("/dashboard")
  async def get_merchant_dashboard(...):
      return {
          "tenant_name": "House of Indya",
          "summary": {
              "active_products": 142,
              "sessions_30d": 4820,
              "tryon_generations_30d": 6140,
              "measured_return_rate_baseline": 31.2,
              "measured_return_rate_with_fit": 27.8,
              "return_reduction_pts": 3.4,
              "estimated_returns_prevented": 614,
              "estimated_cost_savings_inr": 214900.0,
          }, ...
      }
  ```
- **Analysis:** The endpoint returns synthetic marketing figures rather than querying PostgreSQL analytics tables. Furthermore, `settings.enable_b2b` defaults to `False` in `main.py`, so this router is unmounted by default.
- **Architectural Decision:**
  - For Pilot MVP v1.0, merchant self-service web portals are classified as **P1/Deferred** per Phase 1.3 MVP Scope Freeze.
  - Pilot analytics are reported via the newly specified Admin Reporting API ([`docs/api/analytics-reporting-api.md`](../api/analytics-reporting-api.md)) and Celery daily rollups ([`docs/analytics/AGGREGATION_PIPELINE.md`](../analytics/AGGREGATION_PIPELINE.md)).
  - **Required Action:** Replace mock metrics in `b2b/dashboard.py` with real SQL queries during Phase 02.3 or isolate behind feature flag.

---

### GAP-02: Root Conftest Autouse Database Fixture Hangs Locally
- **Location:** [`tests/conftest.py#L104-L125`](file:///c:/Users/ASUS/Documents/FashXStudio/tests/conftest.py#L104-L125)
- **Code Observation:**
  ```python
  @pytest.fixture(autouse=True)
  def setup_test_identity_override():
      engine = create_async_engine("sqlite+aiosqlite:///:memory:", poolclass=StaticPool)
      async def _init_db():
          async with engine.begin() as conn:
              await conn.run_sync(Base.metadata.create_all)
      asyncio.run(_init_db())
      ...
  ```
- **Analysis:**
  - Because `autouse=True` is enabled, this fixture runs before *every* test in the entire repository, including pure unit tests.
  - `Base.metadata` includes PostgreSQL 16-specific types (JSONB, pgvector vectors, partitioned tables). When `Base.metadata.create_all` runs on SQLite in-memory on Windows, it deadlocks or hangs waiting on aiosqlite event loop cleanup.
  - In GitHub Actions CI, PostgreSQL is actively running, and tests marked `db` execute against Postgres. Locally, running pytest without Postgres hangs on collection.
- **Required Action:** Refactor `setup_test_identity_override` in `tests/conftest.py` so it only executes for tests marked with `@pytest.mark.asyncio` or tests that explicitly request client/database fixtures, leaving pure unit tests completely unencumbered.

---

### GAP-03: Live VTO Provider Execution Barred from Automated CI
- **Location:** [`backend/fashx/tryon/adapters/mock_adapter.py`](file:///c:/Users/ASUS/Documents/FashXStudio/backend/fashx/tryon/adapters/mock_adapter.py), [`backend/fashx/infrastructure/tryon/fashn_api.py`](file:///c:/Users/ASUS/Documents/FashXStudio/backend/fashx/infrastructure/tryon/fashn_api.py)
- **Analysis:**
  - Automated tests and CI workflows default to `MockTryOnAdapter`, generating synthetic 100x100 solid JPEG bytes.
  - The live commercial adapter (`fashn_api.py`) is fully implemented with backoff retries, timeouts, and DPA compliance checks, but calling it requires a funded vendor account (`FASHN_API_KEY`).
  - Barring live paid calls from CI is standard practice to prevent runaway cloud expenses and protect user photo privacy.
- **Required Action:** Keep `MockTryOnAdapter` as default in CI. Enforce live FASHN API validation exclusively in the dedicated staging pipeline (`rc08-staging.yml` or manual staging pre-flight) using authorized test fixtures.

---

### GAP-04: FashionCLIP Model Dependency in Recommendation Engine
- **Location:** [`backend/fashx/catalog/embeddings/marqo_fashionclip.py`](file:///c:/Users/ASUS/Documents/FashXStudio/backend/fashx/catalog/embeddings/marqo_fashionclip.py), [`backend/fashx/catalog/embeddings/fake.py`](file:///c:/Users/ASUS/Documents/FashXStudio/backend/fashx/catalog/embeddings/fake.py)
- **Analysis:**
  - The live embedding adapter downloads and executes `Marqo/marqo-fashionCLIP` (ViT-B/32, 512 dimensions).
  - During local development and CI runs, `FakeEmbedder` generates deterministic token-hashed 512-d unit vectors to avoid downloading 600MB model weights and spinning up PyTorch.
- **Required Action:** For Pilot MVP v1.0 with 100–500 SKUs, generate and commit a pre-computed vector embedding fixture in `catalog_seed/` so the recommendation engine can run realistic vector similarity searches without runtime GPU overhead.

---

### GAP-05: Legacy Remote Feature Branches on GitHub
- **Location:** `origin/feat/mvp-readiness` and `origin/feat/slice3-closet-buy-fit`
- **Analysis:**
  - During earlier development cycles, pull requests #30, #31, #32, and #33 merged core features into `main`.
  - However, remote branches `feat/mvp-readiness` and `feat/slice3-closet-buy-fit` remain unmerged on GitHub origin.
- **Required Action:** Perform a commit delta audit against `main` in Phase 02.4 to confirm that all required mobile fixes and database migrations were incorporated, then safely delete or close these stale remote branches.
