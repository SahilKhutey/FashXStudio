# RC-06 — Local Execution & Verification Guide

This guide details how to verify the RC-06 shopping, retailer offer comparison, and purchase handoff pipeline locally.

## Prerequisites
- Python 3.12+ virtualenv (`.venv/`)
- Node.js 20+ and npm in `mobile/`

## 1. Run Backend RC-06 Test Matrix
Execute all 11 test suites covering RC-06 unit, integration, and contract verification:
```powershell
.venv\Scripts\pytest.exe tests/unit/test_rc06_retailer_url.py `
  tests/unit/test_rc06_buy_click.py `
  tests/unit/test_rc06_offer_validation.py `
  tests/unit/test_rc06_price_formatting.py `
  tests/unit/test_rc06_catalog_source_clearance.py `
  tests/integration/test_rc06_shopping_journey.py `
  tests/integration/test_rc06_buy_click_api.py `
  tests/integration/test_rc06_wardrobe_flow.py `
  tests/integration/test_rc06_user_isolation.py `
  tests/contracts/test_rc06_garment_detail_contract.py `
  tests/contracts/test_rc06_offer_contract.py -v
```

## 2. Verify OpenAPI Security Route Snapshot
Ensure no unintended or unauthenticated routes leaked into the API contract:
```powershell
.venv\Scripts\pytest.exe tests/security/test_routes_snapshot.py -v -m "not frozen"
```

## 3. Run Mobile Test Matrix
Execute the full mobile test suite across all 22 test suites:
```powershell
npm --prefix mobile test -- --runInBand
```

Execute the RC-06 Retailer Offers component test suite directly:
```powershell
npm --prefix mobile test -- __tests__/rc06_retailer_offers.test.tsx
```

## 4. Run Mobile TypeScript Typecheck
Verify 100% type safety with zero type errors:
```powershell
npx --prefix mobile tsc -p mobile --noEmit
```

## 5. Run End-to-End Shopping Smoke Test
Run the comprehensive 8-phase shopping verification script:
```powershell
.venv\Scripts\pytest.exe -s scripts/rc06_shopping_smoke.py
```
