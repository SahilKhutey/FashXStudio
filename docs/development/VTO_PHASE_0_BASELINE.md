# FashXStudio VTO — Phase 0 Baseline

**Phase:** VTO-0 — Repository Audit and Development Foundation
**Status:** Completed baseline checks on current local branch
**Purpose:** Establish a reproducible baseline before implementing the end-to-end virtual try-on experience.

## 1. Existing implementation
- [x] Try-on request/output contracts exist (`backend/fashx/application/ports/tryon.py`).
- [x] Hosted FASHN adapter implementation exists (`backend/fashx/infrastructure/tryon/fashn_api.py`).
- [x] Provider configuration exists in core settings (`backend/fashx/core/settings.py`).
- [x] Model-license guard exists (`backend/fashx/ml/licenses.py`).
- [x] Catalog acquisition and image validation exist (`backend/fashx/catalog/`).
- [x] Catalog source rights and try-on eligibility rules are documented (`docs/architecture/catalog-sources.md`).
- [x] Existing adapter unit tests exist (`tests/unit/test_tryon_adapters.py`).
- [x] Current branch and commit recorded locally.
- [x] Focused tests executed on the current checkout (preflight: 7 passed, adapter/use-case: 18 passed, contracts/orchestration: 9 passed, catalog: 14 passed).
- [ ] Actual live provider inference independently verified (unverified; pending live founder credentials).

## 2. Environment and dependencies
Required for local development:
- Python version supported by pyproject.toml (`>=3.12,<3.14`).
- Project development dependencies installed.
- Existing test and lint configuration available.

Required for live inference:
- Authorized provider account and valid API key.
- Provider billing/quota verified.
- A permitted garment image and consented test person image.
- Private storage configured for results.
- Persistent database and worker configured for the full journey.

Never place API keys or person photographs in source control.

## 3. Safety invariants
1. Sources without documented clearance cannot supply production try-on images.
2. A catalog image must be eligible for both display and AI processing.
3. The user must have valid, active body-photo consent.
4. Production must not silently fall back to a mock result.
5. Private try-on artifacts must be authorized by user ownership.
6. Failures must not return another user's image or a vendor-private URL.
7. Deletion and consent revocation must be testable.
8. Visual try-on results must not be represented as guaranteed clothing fit.

## 4. Required evidence
Record the following after execution:
- Git branch and commit SHA
- Python version
- Dependency installation result
- Focused VTO test result
- Lint and documentation-lint results
- Provider configuration state (never the secret value)
- Live inference evidence, if available
- Remaining blockers and owner

## 5. Exit criteria
Phase 0 is complete when:
- Existing modules and contracts have been mapped.
- Focused tests pass, or failures are documented with reproducible details.
- Missing external dependencies are explicitly recorded.
- The initial catalog source and supported garment category are selected.
- Phase 1 can proceed without duplicating existing modules.

Passing Phase 0 does not mean the complete VTO MVP is production-ready.
