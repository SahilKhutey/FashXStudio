> **Development log. Contains no real-world measurements or simulated evidence.**

# Developer Log: Phase 07 VTO Production Architecture & Engineering Notes

**Author**: Coding Agent  
**Date**: November 24, 2026  
**Repository**: `FashXStudio`  
**Branch**: `feat/phase04.5-photo-upload`  

---

## 1. Technical Architecture Decisions

### 1.1 Strict Shopper Privacy vs Global Caching
- **Design Dilemma**: Caching identical garment try-on renders across different users would save compute and third-party API costs.
- **Decision**: Prohibited by architecture. In Virtual Try-On, the output incorporates the shopper's face, body contours, and private photograph. Sharing outputs across users violates GDPR Article 9 (biometric/special category personal data) and CCPA.
- **Resolution**: Every composite cache key cryptographically incorporates `user_id`. Furthermore, `TryOnCacheService` asserts `record.owner_user_id == requesting_user_id` at the database query layer.

### 1.2 Two-Phase Atomic Budget Pre-Reservation
- **Design Dilemma**: In an asynchronous worker cluster, checking budgets *after* provider calls allows worker stampedes to exceed hard budget caps. Debiting budgets *before* inference causes lost credit records on worker crashes.
- **Decision**: Two-phase reservation protocol (`RESERVE` $\rightarrow$ `COMMIT` / `RELEASE`).
- **Resolution**:
  1. `reserve_budget` executes `SELECT ... FOR UPDATE` on the budget row and increments `reserved_spend_usd`.
  2. The worker dispatches the inference request.
  3. Upon success, `commit_reservation` debits `reserved_spend_usd` and credits `current_spend_usd`.
  4. If the job fails before submission, `release_reservation` restores `reserved_spend_usd`.
  5. If the outcome is ambiguous (`SUBMISSION_UNKNOWN`), the reservation is marked `HELD_FOR_RECONCILIATION` until verified.

### 1.3 Category-Specific Release Gates
- **Design Dilemma**: Commercial VTO providers often market universal apparel support, but single-garment 2D diffusion models struggle with complex multi-piece drapes like sarees, lehengas, and layered dupattas.
- **Decision**: Categories are evaluated independently and gated by `is_vto_category_allowed()`.
- **Resolution**:
  - `T-shirts`, `Casual Shirts`, `Kurtas`, `Tops`: Candidate / Controlled Evaluation.
  - `Sarees`, `Lehengas`: Automatically marked `BLOCKED` until dedicated multi-piece drape evidence is established.
  - Shoppers selecting blocked categories receive clear, empathetic notices without backend error crashes.

---

## 2. Engineering Challenges & Solutions

### 2.1 Python Site-Packages `tests` Clash on Windows
- **Issue**: Running `import tests.unit...` caused Python 3.12 to resolve the top-level `tests` package from global `site-packages\tests\__init__.py` (installed by the `ultralytics` package), failing with `PermissionError: Access is denied: ...\Ultralytics\settings.json`.
- **Solution**: Test runners (`run_all_cost_control_tests.py`, `run_all_evaluation_tests.py`) utilize `importlib.util.spec_from_file_location` and register modules under distinct names, bypassing site-packages namespace collision.

### 2.2 Windows Sandbox Asyncio IOCP Deadlocks
- **Issue**: Calling `asyncio.run()` in a tight loop inside the Windows execution sandbox causes the ProactorEventLoop to hang when managing IOCP completions without socket handles.
- **Solution**: Implemented `run_sync(coro)` utilizing synchronous generator stepping (`coro.send(val)`), allowing fully asynchronous coroutines to execute reliably and synchronously in test suites without IOCP polling hangs.

### 2.3 Alembic Schema Hierarchy
- **Sequence**:
  - `0051_add_tryon_lifecycle_and_attempts`
  - `0052_add_tryon_reliability_events_and_dlq`
  - `0053_add_tryon_cache_and_cost_controls`
  - `0054_add_tryon_quality_evaluation`
- **Verification**: Verified using Python runtime AST introspection and migration loader checks. Live execution against PostgreSQL 16 container runs in GitHub Actions CI as required by Rule 14.

---

## 3. Test Verification Command Reference

```bash
# 1. Phase 07.5 Reliability Engine Test Suite (61 tests)
python tests/unit/tryon/lifecycle/run_all_reliability_tests.py

# 2. Phase 07.6 Caching & Cost Control Test Suite (43 tests)
python tests/unit/tryon/cache/run_all_cost_control_tests.py

# 3. Phase 07.7 Quality Evaluation Test Suite (24 tests)
python tests/unit/tryon/evaluation/run_all_evaluation_tests.py

# 4. Code Formatting and Linting
ruff check backend/ database/ tests/
python scripts/docs_lint.py
```
