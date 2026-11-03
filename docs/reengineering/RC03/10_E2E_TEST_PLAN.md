# RC-03 — End-to-End Test Plan & Verification Matrix

## Test Hierarchy

| Layer | Test Target | Command | Result |
|---|---|---|---|
| **Mobile Unit** | Query Keys Isolation | `npm test -- queryKeys.test.ts` | 7 passed |
| **Mobile Unit** | Safe Redirect Security | `npm test -- safeRedirect.test.ts` | 8 passed |
| **Mobile Full** | All 21 Jest Suites | `npm test -- --ci` | 21 passed (152 tests) |
| **Mobile Types** | TypeScript Compiler | `npm run typecheck` | 0 errors |
| **Backend Unit** | Unit Test Suite | `pytest tests/unit -m "not frozen"` | 907 passed |
| **Backend E2E** | System Integration | `pytest tests/integration/test_rc03_e2e_integration.py` | 1 passed |
| **Runtime Smoke** | Multi-step Live Smoke | `python scripts/rc03_smoke.py` | 6/6 passed (exit 0) |

## Verification Evidence Pastes

### 1. Mobile Jest Suite (21/21 Suites Passed)
```
PASS __tests__/runtime_config.test.ts
PASS src/design-system/__tests__/design-system.test.ts
PASS __tests__/closet_and_offers.test.tsx
PASS src/navigation/__tests__/route-policy.test.ts
PASS src/lib/__tests__/safeRedirect.test.ts
PASS __tests__/auth_and_api.test.ts
PASS __tests__/onboarding_schemas.test.ts
PASS src/app-shell/__tests__/queryKeys.test.ts
PASS __tests__/tryon_polling.test.ts
PASS src/api/client.test.ts
PASS __tests__/tryon_screen.test.tsx
PASS __tests__/capture_privacy.test.ts
PASS __tests__/file_cleanup.test.ts
PASS __tests__/quality_reasons.test.ts
PASS src/features/wardrobe/__tests__/commerceApi.test.ts
PASS __tests__/style_quiz_picks.test.ts
PASS __tests__/dev_token_gate.test.ts
PASS src/design-system/components/__tests__/Button.test.tsx
PASS __tests__/feed_and_tryon.test.ts
PASS __tests__/tryon_feedback.test.ts
PASS __tests__/settings_and_privacy.test.ts

Test Suites: 21 passed, 21 total
Tests:       152 passed, 152 total
Snapshots:   0 total
Time:        9.303 s
```

### 2. Runtime Smoke Verification Output (`python scripts/rc03_smoke.py`)
```
=== FashXStudio RC-03 Smoke Verification against http://localhost:8000 ===

[1/6] Verifying Health & Readiness probes...
  + /healthz/live: OK (status=ok)
  + /healthz/ready: OK (status=ok, db=ok)

[2/6] Generating Demo JWT & Verifying User Identity...
  + /api/v1/me: Authenticated as user_id=15c0ef47-6be9-4309-9973-cd83a29bd0b7 (roles=['user'])

[3/6] Verifying Discovery Feed...
  + /api/v1/feed: Loaded 20 garments. First: 'Women's White Cotton Stretch Leggings' (id=909b4b39-ee8d-4bf5-b32d-d525850c88a0)

[4/6] Verifying Outbound Commerce Affiliate Redirect...
  + /api/v1/commerce/buy-clicks: Success (tracking_id=fashx_15c0ef47_37ca43dfc3, redirect=https://shop.example.com/products/g014?utm_source=fashx&utm_...)

[5/6] Verifying Wardrobe Persistence (Save, List, Remove)...
  + Saved garment to closet: item_id=77357076-fc75-45da-adf1-0ace640a4567
  + Wardrobe query verified: item exists in user wardrobe
  + Wardrobe item removed cleanly (HTTP 204)

[6/6] Verifying Virtual Try-On Jobs query...
  + /api/v1/tryon/jobs: Query successful (total existing jobs=0)

=======================================================
SUCCESS: ALL RC-03 SYSTEM INTEGRATION WORKFLOWS VERIFIED
=======================================================
```
