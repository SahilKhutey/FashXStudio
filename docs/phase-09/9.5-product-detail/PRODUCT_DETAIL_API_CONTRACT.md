# Product Detail API Contract

- `GET /api/v1/catalog/products/{product_id}/detail?offer_id={offer_id}` (`fetchProductDetail`)
- `GET /api/v1/catalog/products/{product_id}/size-chart?offer_id={offer_id}` (`fetchProductSizeChart`)
- `POST /api/v1/catalog/offers/{offer_id}/redirect` (`requestMerchantRedirect`)
- `POST /api/v1/wardrobe/items` & `DELETE /api/v1/wardrobe/items/{item_id}` (existing `mobile/src/features/wardrobe/api.ts`)
- Existing `/api/v1/garments/{id}` (`backend/fashx/catalog/customer_router.py`) preserved for `/garment/[id]`.
