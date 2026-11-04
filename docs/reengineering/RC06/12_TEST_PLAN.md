# RC-06 — Test Plan & Quality Gates

## Verification Architecture

The RC-06 shopping verification matrix encompasses unit tests, API integration tests, contract compliance tests, mobile component tests, and an automated end-to-end smoke verification harness.

### 1. Backend Test Suites

| Suite | Scope | File | Test Count |
|---|---|---|---|
| **Retailer URL Security** | Protocol, credentials, allowlist matching, lookalike attack defense | `tests/unit/test_rc06_retailer_url.py` | 8 |
| **Buy Click Logic** | Active garment, in-stock check, source clearance, user binding | `tests/unit/test_rc06_buy_click.py` | 7 |
| **Offer Ranking** | In-stock prioritization, price sorting, fallback display price | `tests/unit/test_rc06_offer_validation.py` | 4 |
| **Price Formatting** | Minor units (paise/cents), negative price rejection, currency | `tests/unit/test_rc06_price_formatting.py` | 3 |
| **Catalog Clearance** | Source status policy enforcement (`cleared` vs `pending`/`revoked`) | `tests/unit/test_rc06_catalog_source_clearance.py` | 4 |
| **Shopping Journey** | Full discovery, offer ranking, buy-click, wardrobe persistence | `tests/integration/test_rc06_shopping_journey.py` | 1 |
| **Buy Click API** | Mandatory offer_id, spoofed user_id rejection (403) | `tests/integration/test_rc06_buy_click_api.py` | 2 |
| **Wardrobe Flow** | Wardrobe save, listing, and delete lifecycle | `tests/integration/test_rc06_wardrobe_flow.py` | 1 |
| **User Isolation** | Cross-user wardrobe, cart (T19), and checkout (T20) isolation | `tests/integration/test_rc06_user_isolation.py` | 2 |
| **Garment Detail Contract** | Pydantic contract serialization, extra fields forbidden | `tests/contracts/test_rc06_garment_detail_contract.py` | 3 |
| **Offer Contract** | Offer serialization, required field validation | `tests/contracts/test_rc06_offer_contract.py` | 2 |

**Total Backend Tests:** 37 passing.

### 2. Mobile Test Suites

| Suite | Scope | File | Test Count |
|---|---|---|---|
| **Retailer Offers Component** | Offer selection, price formatting, CTA disabled state, safe redirect | `mobile/__tests__/rc06_retailer_offers.test.tsx` | 13 |
| **Safe Redirect Utility** | Client-side URL validation against open redirect attacks | `mobile/src/lib/__tests__/safeRedirect.test.ts` | 8 |
| **Commerce API Client** | Buy-click API payload and response contract | `mobile/src/features/wardrobe/__tests__/commerceApi.test.ts` | 4 |
| **Full Mobile Suite** | All Expo client test suites across navigation, design system, try-on | `mobile/__tests__/` | 165 total (22 suites) |

### 3. End-to-End System Smoke Test
- **Script:** `scripts/rc06_shopping_smoke.py`
- **Scope:** 8 complete phases: health probes, identity authentication, catalog seeding, multi-offer comparison, buy-click handoff, wardrobe save, wardrobe removal, and cross-user isolation.
