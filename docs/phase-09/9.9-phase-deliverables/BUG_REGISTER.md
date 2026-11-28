# Phase 09.9 Bug & Integration Gap Register

| ID | Severity | Area | Summary | Status |
|---|---|---|---|---|
| `BUG-09-00` | Medium | `mobile/src/services/crashReporting.ts` | `SENSITIVE_PATTERN` stopped redacting signed URLs at `X-Amz-Signature`, leaving `=deadbeef` query value unredacted. Fixed regex to consume `[^\s]*` after signature/amz marker. | `FIXED` (verified in `phase09_9_exit_gate.test.tsx`) |
| `BUG-09-01` | High | `backend/fashx/main.py` vs `catalog/detail/router.py` | `catalog/detail/router.py` (`/catalog/products/{product_id}/detail`, `/catalog/offers/{offer_id}/redirect`) is tested in isolation but not yet mounted in `create_app()`. | `OPEN` |
| `BUG-09-02` | High | `backend/fashx/main.py` vs `commerce_wardrobe/looks/router.py` | `commerce_wardrobe/looks/router.py` (`/wardrobe/looks`) is tested in isolation but not yet mounted in `create_app()`. | `OPEN` |
| `BUG-09-03` | Medium | `backend/fashx/api/v1/onboarding.py` | `onboardingService.getProgress()` calls `GET /api/v1/onboarding/progress`, which is not yet mounted alongside `/onboarding/style-quiz`. | `OPEN` |
