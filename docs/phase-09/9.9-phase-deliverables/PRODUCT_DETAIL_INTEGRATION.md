# Product Detail Integration

- **Merchant Offer Isolation**: `fetchProductDetail(productId, offerId)` (`mobile/src/features/product-detail/api.ts`) queries `/catalog/products/{productId}/detail?offer_id={offerId}`, keeping price, stock, and outbound link bound to the specific merchant offer.
- **Availability Messaging**: `availabilityMessage()` and `canPurchase()` (`mobile/src/features/product-detail/utils/availability.ts`) map `in_stock`, `low_stock`, `out_of_stock`, `pre_order`, `stale`, `delisted`, and `taken_down` cleanly.
- **Size Charts**: `fetchProductSizeChart(productId, offerId)` fetches merchant size charts separately from live variant stock.
- **Known Gap**: `backend/fashx/catalog/detail/router.py` exists and passes unit tests (`tests/unit/catalog/test_phase09_5_pdp_redirect.py`), but needs to be mounted in `backend/fashx/main.py` before staging E2E testing.
