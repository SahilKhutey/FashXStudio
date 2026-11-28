# Phase 09.5 Test Plan

- Backend: `tests/unit/catalog/test_phase09_5_pdp_redirect.py` (`validate_merchant_url` HTTPS/domain/credentials/lookalike tests, `ProductAttributeResponse`, `ProductAvailability`).
- Mobile: `mobile/src/features/product-detail/__tests__/pdp.test.tsx` (`formatMinorPrice`, `getDiscountPercentage`, `availabilityMessage`, `canPurchase`, `ProductGallery`, `fetchProductDetail`, `requestMerchantRedirect`).
- Live Postgres detail/redirect endpoints and physical Android/iOS device QA remain `PENDING`.
