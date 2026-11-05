# RC-06 — Shopping, Retailer Offers & Purchase Handoff

## Mission
Take FashXStudio from a working Virtual Try-On experience (RC-05) to a complete shopping journey: users discover garments, compare real retailer offers, check availability, save items to their digital closet, and continue to an external retailer's purchase page with verified affiliate attribution.

## Baseline
- **Base Branch:** `recovery/rc05-vto-integration`
- **Baseline Commit:** `e6c98a58e26bc7d0e4130be1e7da9e17ba935d25`
- **Implementation Branch:** `recovery/rc06-shopping-integration`

## Scope
1. **Garment Detail & Offer Aggregation:** Customer garment endpoint exposes verified multi-merchant offers, actual offer price in integer minor units (paise for INR), currency, stock status, and real sync timestamps.
2. **Multi-Offer Ranking Engine:** In-stock offers prioritized first, then sorted ascending by price. Display price computed as the lowest in-stock offer price.
3. **Retailer URL Security:** Outbound links strictly validated for HTTPS, credentials rejected, lookalikes blocked, and domain allowlist enforced (fails closed in production).
4. **Attributed Buy-Click Handoff:** `/commerce/buy-clicks` requires explicit `garment_id` AND `offer_id` (mandatory offer selection; no generic fallback). Caller identity bound to JWT principal.
5. **Attribution Parameters:** Automatically attaches `utm_source=fashx`, `utm_medium=app`, `utm_campaign=vto_purchase`, `sub_id=<user_id>`, and `click_id=<buy_click_id>`.
6. **Catalog Clearance Policy:** Inactive garments rejected. Uncleared catalog sources (`pending`, `revoked`, `review`) rejected from commerce handoff.
7. **Cart & Checkout Hardening:** Audited and hardened customer cart (T19) and checkout session (T20) endpoints against cross-user tampering.
8. **Wardrobe Integration:** Save to wardrobe captures immutable snapshot price and title; list and delete operations scoped to caller.
9. **Mobile Reconstruction:** React Native Expo components (`RetailerOffers.tsx`, `useBuy.ts`, `buyClickApi.ts`, `garment/[id].tsx`) updated for explicit offer selection, accessibility, and client-side URL safety.
10. **Automated Verification:** Comprehensive test matrix spanning 11 backend test suites (37 tests), 22 mobile test suites (165 tests), TypeScript type safety, and OpenAPI route snapshots.

## Scope Boundaries & Commerce Boundary Rule
- **Decision vs Execution:** FashX helps users decide what to buy; the external retailer remains responsible for stock, checkout, payment, and order fulfillment.
- **Attribution vs Sale:** An outbound buy-click is an attribution handoff, NEVER proof of purchase. FashX must never simulate, mock, or emit `purchase_confirmed` without verified affiliate conversion postback data.
- **Mandatory Offer Selection:** Users cannot initiate a purchase handoff without selecting an explicit retailer offer.

## Verified Results Summary
| Verification Target | Command | Result |
|---|---|---|
| **Backend RC-06 Suites** | `pytest tests/unit/test_rc06_*.py tests/integration/test_rc06_*.py tests/contracts/test_rc06_*.py -v` | 🟢 37/37 passed in 9.60s |
| **Mobile Jest Suites** | `npm --prefix mobile test -- --runInBand` | 🟢 22/22 suites passed (165/165 tests in 11.167s) |
| **Mobile TypeScript Typecheck** | `npx --prefix mobile tsc -p mobile --noEmit` | 🟢 0 errors |
| **OpenAPI Security Snapshot** | `pytest tests/security/test_routes_snapshot.py -v -m "not frozen"` | 🟢 2 passed in 2.68s |

## Documentation Index
- [00_SCOPE_AND_BASELINE.md](00_SCOPE_AND_BASELINE.md)
- [01_SHOPPING_ARCHITECTURE.md](01_SHOPPING_ARCHITECTURE.md)
- [02_CATALOG_AND_DISCOVERY.md](02_CATALOG_AND_DISCOVERY.md)
- [03_GARMENT_DETAIL_CONTRACT.md](03_GARMENT_DETAIL_CONTRACT.md)
- [04_RETAILER_OFFER_COMPARISON.md](04_RETAILER_OFFER_COMPARISON.md)
- [05_PRICE_AND_AVAILABILITY.md](05_PRICE_AND_AVAILABILITY.md)
- [06_WARDROBE_INTEGRATION.md](06_WARDROBE_INTEGRATION.md)
- [07_BUY_CLICK_AND_REDIRECT.md](07_BUY_CLICK_AND_REDIRECT.md)
- [08_AFFILIATE_ATTRIBUTION.md](08_AFFILIATE_ATTRIBUTION.md)
- [09_CART_CHECKOUT_SECURITY.md](09_CART_CHECKOUT_SECURITY.md)
- [10_MOBILE_INTEGRATION.md](10_MOBILE_INTEGRATION.md)
- [11_ANALYTICS.md](11_ANALYTICS.md)
- [12_TEST_PLAN.md](12_TEST_PLAN.md)
- [13_EXECUTION_GUIDE.md](13_EXECUTION_GUIDE.md)
- [14_ACCEPTANCE_REPORT.md](14_ACCEPTANCE_REPORT.md)
- [tasks/RC06_TASK_LIST.md](tasks/RC06_TASK_LIST.md)

## Status
🟢 **READY FOR FOUNDER REVIEW & PR MERGE** — All automated criteria, security gates, and integration test suites pass.
