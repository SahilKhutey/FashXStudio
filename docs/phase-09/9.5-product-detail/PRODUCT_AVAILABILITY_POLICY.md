# Product Availability Policy

- `ProductAvailability` enum (`in_stock`, `low_stock`, `out_of_stock`, `pre_order`, `unknown`, `stale`, `delisted`, `taken_down`) shared between `backend/fashx/catalog/detail/schemas.py` and `mobile/src/features/product-detail/types.ts`.
- `unknown` is never treated as `in_stock`.
