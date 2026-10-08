# Phase 2C Task Log: Frozen Scope Gating & Mobile Consolidation

**Date:** 2026-10-08  
**Branch:** `chore/phase2c-freeze-mobile`  
**Goal:** Gate frozen post-MVP commerce modules (C05–C11) behind `FASHX_ENABLE_FROZEN`, establish test suite partitioning (1,027 MVP / 244 frozen), consolidate mobile applications into a single canonical `mobile/` directory, and update CI workflows.

---

## 1. Scope Gating Audit & Implementation
- **Dependency Audit:** Evaluated all imports across active backend modules. Confirmed zero MVP domains depend on frozen commerce modules.
- **Router Gating:** In `backend/fashx/main.py`, 8 post-MVP routers (`inventory`, `promotions`, `cart`, `checkout`, `orders`, `payments`, `fulfillment`, `returns`) are now mounted conditionally:
  ```python
  enable_frozen = settings.enable_frozen or os.getenv("FASHX_ENABLE_FROZEN", "0") == "1"
  if enable_frozen: ...
  ```
- **OpenAPI Surface:**
  - `FASHX_ENABLE_FROZEN=0` (default): 206 routes
  - `FASHX_ENABLE_FROZEN=1`: 233 routes (27 commerce endpoints mounted)
- **Settings & Environment:** Added `enable_frozen: bool` to `fashx.core.settings.Settings` and `FASHX_ENABLE_FROZEN=0` to `.env.example`.

---

## 2. Test Partitioning
- **Marker Setup:** In `tests/conftest.py` and `pytest.ini`, registered and automated the `frozen` pytest marker.
- **Verification:**
  - `pytest -m "not frozen"`: **1,027 passed, 244 deselected** in 14.94s (clean MVP core).
  - `pytest -m "frozen"`: **244 passed, 1,027 deselected** in 4.80s.
  - Sum: 1,027 + 244 = **1,271 tests (100% pass rate, 0 failures, 0 skips)**.

---

## 3. Mobile Consolidation
- Audited `apps/mobile/` (old Expo 51 stub with 12 files) against `mobile/` (canonical Expo 57 app with 229 TypeScript/TSX files).
- Removed obsolete directory `apps/mobile/`.
- Consolidated on canonical `mobile/`.

---

## 4. CI Workflow Modernization (`.github/workflows/ci.yml`)
- `backend` job: required gate running `pytest -m "not frozen"`, `alembic heads`, `alembic upgrade head`, `mypy .`, and `ruff check . --exit-zero`.
- `frozen` job: non-blocking test runner (`continue-on-error: true`) with `FASHX_ENABLE_FROZEN=1` running `pytest -m "frozen"`.
- `mobile` job: runs Node 20 build and typecheck in `mobile/`.
