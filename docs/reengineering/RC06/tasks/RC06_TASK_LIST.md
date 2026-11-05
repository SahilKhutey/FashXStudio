# RC06 Implementation Task List & Tracking Register

**Target Branch:** `recovery/rc06-shopping-integration`  
**Base Commit:** `e6c98a58e26bc7d0e4130be1e7da9e17ba935d25` (`recovery/rc05-vto-integration`)  
**Status:** Completed (Pending Final PR Review)

---

## RC06.0 — Baseline & Repository Checkout
- [x] Create RC06 branch from `recovery/rc05-vto-integration` (`recovery/rc06-shopping-integration`)
- [x] Audit baseline commerce routes, models, schemas, and buy-click implementation
- [x] Establish boundary rule: FashX helps decide what to buy; external retailer handles checkout and fulfillment

## RC06.1 — Multi-Merchant Offers & Garment Detail
- [x] **RC06-T01**: Extend `CustomerOfferDetail` schema with `merchant_name: str | None` and `updated_at: datetime | None`
- [x] **RC06-T02**: Resolve merchant name from `merchants` table via foreign key
- [x] **RC06-T03**: Populate `updated_at` from `MerchantOffer.last_synced_at` (no fabricated dates)
- [x] **RC06-T04**: Implement multi-offer ranking: in-stock first, ascending price order
- [x] **RC06-T05**: Compute canonical `display_price` as lowest in-stock offer price (or fallback if all out of stock)
- [x] **RC06-T06**: Add contract test `tests/contracts/test_rc06_garment_detail_contract.py`
- [x] **RC06-T07**: Add contract test `tests/contracts/test_rc06_offer_contract.py`

## RC06.2 — Price Standards & Currency Formatting
- [x] **RC06-T08**: Enforce integer minor units (`price_minor`) across all models and APIs
- [x] **RC06-T09**: Reject negative prices (`Field(ge=0)`) at validation layer
- [x] **RC06-T10**: Add test suite `tests/unit/test_rc06_price_formatting.py` (INR, USD, EUR, negative validation)

## RC06.3 — Retailer URL Validation & Security
- [x] **RC06-T11**: Implement `validate_retailer_url` in `create_buy_click.py`
- [x] **RC06-T12**: Enforce strict HTTPS protocol (reject http, javascript, ftp, data)
- [x] **RC06-T13**: Reject embedded credentials (`user:pass@host`)
- [x] **RC06-T14**: Block lookalike hostnames and domain suffix confusion
- [x] **RC06-T15**: Enforce production allowlist (`FASHX_RETAILER_ALLOWED_HOSTS`) with fail-closed behavior
- [x] **RC06-T16**: Add unit test suite `tests/unit/test_rc06_retailer_url.py` (8/8 passed)

## RC06.4 — Outbound Purchase Handoff & Buy-Click API
- [x] **RC06-T17**: Require explicit `garment_id` AND `offer_id` in `BuyClickRequest` (remove generic fallback)
- [x] **RC06-T18**: Reject out-of-stock offer buy-clicks with `409 Conflict`
- [x] **RC06-T19**: Bind user identity strictly to JWT principal (`effective_user_id`); reject spoofed user_id with `403 Forbidden`
- [x] **RC06-T20**: Append attribution parameters (`utm_source`, `utm_medium`, `utm_campaign`, `sub_id`, `click_id`)
- [x] **RC06-T21**: Enforce catalog source clearance (`status="cleared"` and `rights_display=True`)
- [x] **RC06-T22**: Add test suite `tests/unit/test_rc06_buy_click.py` (7/7 passed)
- [x] **RC06-T23**: Add test suite `tests/integration/test_rc06_buy_click_api.py` (2/2 passed)

## RC06.5 — Cart & Checkout Security Hardening
- [x] **RC06-T24**: Enforce customer cart ownership checks in `backend/fashx/api/v1/cart.py`
- [x] **RC06-T25**: Enforce checkout session ownership checks in `backend/fashx/api/v1/checkout.py`
- [x] **RC06-T26**: Add test suite `tests/integration/test_rc06_user_isolation.py` (2/2 passed)

## RC06.6 — Wardrobe Lifecycle Integration
- [x] **RC06-T27**: Capture immutable snapshot title and price minor on `POST /wardrobe/items`
- [x] **RC06-T28**: Verify wardrobe save, list, and removal lifecycle (`tests/integration/test_rc06_wardrobe_flow.py`)

## RC06.7 — Mobile Client Reconstruction
- [x] **RC06-T29**: Update `mobile/src/features/wardrobe/RetailerOffers.tsx` with accessible radio controls and merchant title fallback
- [x] **RC06-T30**: Implement `formatOfferPrice` in mobile supporting INR, USD, EUR, and multi-currency formatting
- [x] **RC06-T31**: Update `mobile/src/features/commerce/useBuy.ts` and `buyClickApi.ts` for explicit `{ garment_id, offer_id }`
- [x] **RC06-T32**: Wire `handleBuy(offerId)` in `mobile/app/garment/[id].tsx` and remove generic bottom bar buy button
- [x] **RC06-T33**: Harden `isSafeRetailerRedirect` in `mobile/src/lib/safeRedirect.ts` against localhost and loopback targets
- [x] **RC06-T34**: Add mobile component test suite `mobile/__tests__/rc06_retailer_offers.test.tsx` (13/13 passed)
- [x] **RC06-T35**: Verify full mobile Jest test suite (22/22 suites, 165/165 passed)
- [x] **RC06-T36**: Verify mobile TypeScript compilation (`tsc -p mobile --noEmit`: 0 errors)

## RC06.8 — Complete Documentation & End-to-End Verification
- [x] **RC06-T37**: Implement comprehensive 8-phase shopping smoke test in `scripts/rc06_shopping_smoke.py`
- [x] **RC06-T38**: Author complete 15-document RC06 package under `docs/reengineering/RC06/`
- [x] **RC06-T39**: Verify OpenAPI security route snapshot (`tests/security/test_routes_snapshot.py`)
