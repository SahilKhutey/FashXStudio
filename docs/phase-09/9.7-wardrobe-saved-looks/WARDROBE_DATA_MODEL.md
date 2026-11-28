# Wardrobe Data Model

- Discriminates `WardrobeItemType` (`PRODUCT` vs `VTO_RESULT`) via `SaveWardrobeItemRequest` (`backend/fashx/commerce_wardrobe/looks/schemas.py`).
- `PRODUCT` requires `product_id` and `offer_id` (forbids `tryon_job_id`); `VTO_RESULT` requires `tryon_job_id` (forbids `product_id`/`offer_id`).
