# Phase 09.7 Test Plan

- Backend: `tests/unit/wardrobe/test_phase09_7_saved_looks.py` (`SaveWardrobeItemRequest` discrimination, `CreateSavedLookRequest` blank-title rejection, `LookOwnershipError` cross-user rejection, deduplication).
- Mobile: `mobile/src/features/wardrobe/__tests__/phase09_7_wardrobe.test.tsx` (`wardrobeKeys`, Saved Looks APIs, `EmptyCloset`, `EmptyLooks`) + existing `closet_and_offers.test.tsx` & `commerceApi.test.ts`.
- Live Postgres Saved Looks tables/endpoints and physical device persistence QA remain `PENDING`.
