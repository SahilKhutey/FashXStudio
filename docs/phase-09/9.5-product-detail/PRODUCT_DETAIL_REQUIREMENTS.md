# Product Detail Requirements

- Separate canonical garment (`garment_id`), merchant product (`merchant_product_id`), and merchant offer (`offer_id`).
- No sample-product fallback on unknown product IDs (`404` returned).
- Independent permissions: `display_allowed`, `vto_allowed`, `redirect_allowed`.
- Unavailable states (`delisted`, `taken_down`, `out_of_stock`, `stale`, `unknown`) remain distinct and understandable.
