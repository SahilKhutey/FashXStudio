# Saved Look Policy

- `create_saved_look_for_user()` (`backend/fashx/commerce_wardrobe/looks/service.py`) deduplicates `item_ids`, verifies every item belongs to `user_id`, and rejects foreign items atomically with `LookOwnershipError`.
