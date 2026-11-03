# RC-00 Findings Register

## Severity Classifications
- **P0**: Prevents a critical MVP user journey.
- **P1**: Major functional or UX degradation.
- **P2**: Moderate issue or incomplete enhancement.
- **P3**: Minor issue or technical debt.

## Finding Statuses
- **CONFIRMED**: Reproduced with runtime/code evidence.
- **RISK**: Potential failure identified but not reproduced.
- **UNVERIFIED**: Evidence is insufficient.
- **RESOLVED**: Fix implemented and retested.
- **WONT_FIX**: Explicitly accepted limitation.

---

### FX-001 — Feed has no product results (Unpopulated Catalog)
- **Subsystem**: Catalog / Discovery
- **Severity**: P0
- **Status**: CONFIRMED
- **Evidence**: `fashx_local.db` has 0 rows in `canonical_garments`, `merchant_products`, `merchant_offers`.
- **Root Cause**: `scripts/catalog/seed_local.py` failed because source `'own-wardrobe'` was never registered or cleared in SQLite.
- **Proposed Correction**: Register source `'own-wardrobe'`, clear consent status, and run `seed_local.py --apply`.
- **Assigned Phase**: RC-01

### FX-003 — Closet has no saved items
- **Subsystem**: Wardrobe
- **Severity**: P0
- **Status**: CONFIRMED
- **Evidence**: `fashx_local.db` table `wardrobe_items` count is 0.
- **Root Cause**: Feed was empty, preventing users from saving products or try-on renders to their wardrobe.
- **Proposed Correction**: Hydrate catalog, verify `POST /api/v1/wardrobe/items` and `GET /api/v1/wardrobe/items` in mobile app.
- **Assigned Phase**: RC-03

### FX-004 — VTO Async Dispatch Deferred in Non-Celery Development
- **Subsystem**: Try-On / ML
- **Severity**: P0
- **Status**: CONFIRMED
- **Evidence**: `backend/fashx/tryon/ports_dispatch.py` silently defers dispatch when Celery/Redis is unreachable.
- **Root Cause**: Lack of in-process fallback dispatcher for local developer workstations.
- **Proposed Correction**: Support direct/async background job dispatcher in local dev runtime.
- **Assigned Phase**: RC-02

### FX-005 — Physical-Device API URL Configuration
- **Subsystem**: Mobile Runtime
- **Severity**: P0
- **Status**: CONFIRMED
- **Evidence**: `mobile/.env` configures `EXPO_PUBLIC_API_URL=http://10.178.234.242:8000`.
- **Root Cause**: Hardcoded Wi-Fi IP address breaks if development machine subnet changes.
- **Proposed Correction**: Add dynamic LAN resolution script and update `.env` CORS origins.
- **Assigned Phase**: RC-06

### FX-009 — Settings Screen Exposes Internal Database UUIDs
- **Subsystem**: Mobile / UI
- **Severity**: P1
- **Status**: CONFIRMED
- **Evidence**: `mobile/app/settings/index.tsx` displays raw `userId` and `photo.id` strings.
- **Root Cause**: Developer diagnostics placed directly into the consumer settings card.
- **Proposed Correction**: Redesign settings into consumer account controls and privacy preferences.
- **Assigned Phase**: RC-04

### FX-010 — Fragmented Navigation Architecture
- **Subsystem**: Mobile / Navigation
- **Severity**: P1
- **Status**: CONFIRMED
- **Evidence**: `mobile/app/(tabs)/_layout.tsx` registers only Feed, Looks, and Closet.
- **Root Cause**: Primary navigation does not include Search, Try-On, or Profile tabs.
- **Proposed Correction**: Rebuild 5-tab navigation shell (Discover, Search, Try-On, Closet, Profile).
- **Assigned Phase**: RC-04
