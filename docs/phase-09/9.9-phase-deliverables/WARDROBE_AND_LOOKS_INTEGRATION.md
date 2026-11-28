# Wardrobe and Looks Integration

- **Closet Items**: `fetchUserWardrobe`, `saveGarmentToWardrobe`, and `removeGarmentFromWardrobe` (`mobile/src/features/wardrobe/api.ts`) connect to `/api/v1/wardrobe/items`.
- **Saved Looks**: `getSavedLooks`, `createSavedLook`, and `deleteSavedLook` connect to `/api/v1/wardrobe/looks`, paired with `mobile/app/wardrobe/looks/create.tsx` and `backend/fashx/commerce_wardrobe/looks/service.py` (`create_saved_look_for_user` enforces item ownership per `user_id`).
- **Account-Scoped Cache**: `wardrobeKeys.items(userId)` and `wardrobeKeys.looks(userId)` (`mobile/src/features/wardrobe/hooks.ts`) key TanStack Query caches by `userId`.
- **Known Gap**: `backend/fashx/commerce_wardrobe/looks/router.py` passes unit tests (`tests/unit/wardrobe/test_phase09_7_saved_looks.py`, `test_phase09_exit_gate.py`) but is not yet mounted in `backend/fashx/main.py`.
