# MVP 5: Closet & Shopping Journey Verification

## Implementation Overview

MVP 5 turns FashXStudio from a fashion discovery and virtual try-on prototype into a personal wardrobe and shopping assistant. It establishes server-governed wardrobe management, database uniqueness constraints, idempotent saves under concurrent requests, secure short-lived signed URLs for wardrobe item snapshots, retailer destination validation for outbound buy-clicks, try-on history ownership enforcement, and mobile integration.

### Key Changes

1. **Server-Controlled Identity & Caller Validation**:
   - `POST /wardrobe/items` ignores or strictly validates any client-provided `user_id` against the authenticated caller (`principal.user_id`).
   - If an explicit `user_id` is supplied in the request payload that does not match `principal.user_id`, the endpoint fails closed with HTTP 403 `forbidden`.
   - When omitted, `user_id` is automatically populated from `principal.user_id`.

2. **Database Uniqueness & Concurrency Idempotency**:
   - Added unique constraint `uq_wardrobe_user_garment` on `("user_id", "garment_id")` in `wardrobe_items` via migration `0030_wardrobe_user_garment_unique.py` (`database/migrations/versions/0030_wardrobe_user_garment_unique.py`).
   - In `SaveToWardrobeUseCase` (`backend/fashx/commerce_wardrobe/application/save_to_wardrobe.py`), wrapped item creation in concurrency-safe handling: if an `IntegrityError` is raised due to a concurrent duplicate save, the session rolls back and returns the existing saved record idempotently.

3. **Secure Image Delivery via Short-Lived Signed URLs**:
   - Updated `SaveToWardrobeUseCase` and `ListWardrobeUseCase` (`backend/fashx/commerce_wardrobe/application/list_wardrobe.py`) to inject storage.
   - Generates signed URLs (`storage.signed_get_url(snapshot_image_key, ttl_s=900)`) for wardrobe item snapshot images.
   - Added `GET /wardrobe/items` returning `{"items": [...]}` with signed `image_url` for the authenticated principal.
   - Preserved `GET /wardrobe/users/{user_id}` and `DELETE /wardrobe/users/{user_id}/items/{item_id}` for backward compatibility with ownership checks.

4. **Retailer Handoff & Outbound URL Validation**:
   - In `backend/fashx/commerce_wardrobe/application/create_buy_click.py`:
     - Added `validate_retailer_url(url: str, allowed_hosts: set[str] | None = None) -> None`: enforces HTTPS scheme, validates presence of hostname, rejects embedded user credentials (preventing credential phishing), and checks hostnames against allowed retailer domains.
     - Enforces that `offer.garment_id == cmd.garment_id` to prevent cross-product tracking mismatches.
     - Validates source clearance status (rejecting unverified or blocked catalog sources).

5. **Try-On History Verification**:
   - Verified `GET /tryon/jobs` enforces authenticated ownership (`principal.user_id`) and returns short-lived signed URLs for completed artifacts.

6. **Mobile Integration**:
   - Updated `mobile/src/features/wardrobe/api.ts` to call `/wardrobe/items` without sending a client-trusted `user_id`.
   - Added `useRemoveFromWardrobe` mutation hook to `mobile/src/features/wardrobe/hooks.ts`.
   - Updated `mobile/app/(tabs)/closet.tsx` to render signed `image_url` (with fallback to `snapshot_image_key`) and wired an action button to remove items with optimistic UI invalidation.

---

## Automated Test Verification

Command:
```powershell
python -c "import pytest; print(pytest.main(['tests/unit/test_mvp5_closet_shopping_journey.py', 'tests/unit/test_wardrobe_use_cases.py', 'tests/unit/test_affiliate_handoff.py', 'tests/contracts/test_wardrobe_repo.py', '-v']))"
```

Output:
```
============================= test session starts =============================
platform win32 -- Python 3.12.10, pytest-9.1.1, pluggy-1.6.0 -- C:\Users\ASUS\AppData\Local\Programs\Python\Python312\python.exe
hypothesis profile 'default'
rootdir: C:\Users\ASUS\Documents\FashXStudio
configfile: pytest.ini
plugins: anyio-4.12.1, hypothesis-6.156.6, langsmith-0.14.4, asyncio-1.4.0, cov-7.1.0
asyncio: mode=Mode.AUTO, debug=False, asyncio_default_fixture_loop_scope=None, asyncio_default_test_loop_scope=function
collecting ... collected 11 items

tests/unit/test_mvp5_closet_shopping_journey.py::test_wardrobe_save_derives_user_from_principal PASSED [  9%]
tests/unit/test_mvp5_closet_shopping_journey.py::test_wardrobe_save_rejects_user_id_mismatch PASSED [ 18%]
tests/unit/test_mvp5_closet_shopping_journey.py::test_wardrobe_save_idempotency_and_uniqueness PASSED [ 27%]
tests/unit/test_mvp5_closet_shopping_journey.py::test_list_my_wardrobe_endpoint PASSED [ 36%]
tests/unit/test_mvp5_closet_shopping_journey.py::test_remove_from_wardrobe_ownership_enforcement PASSED [ 45%]
tests/unit/test_retailer_url_validation PASSED [ 54%]
tests/unit/test_mvp5_closet_shopping_journey.py::test_buy_click_validates_garment_offer_relationship PASSED [ 63%]
tests/unit/test_mvp5_closet_shopping_journey.py::test_tryon_history_lists_user_jobs_with_signed_urls PASSED [ 72%]
tests/unit/test_wardrobe_use_cases.py::test_wardrobe_save_list_and_remove PASSED [ 81%]
tests/unit/test_affiliate_handoff.py::test_affiliate_handoff_and_tracking_id PASSED [ 90%]
tests/contracts/test_wardrobe_repo.py::test_wardrobe_price_snapshot_and_retrieval PASSED [100%]

============================= 11 passed in 8.16s ==============================
0
```

---

## Environment & Gate Compliance Note

- Unit tests and contract tests executed and passed hermetically with SQLite test fixtures.
- In accordance with repository Rule 14, Docker and a local PostgreSQL daemon on localhost:5432 are not active in this development environment; execution of `scripts/ci/local_gate.sh` and full database migrations against PostgreSQL will run in the GitHub Actions CI pipeline.
