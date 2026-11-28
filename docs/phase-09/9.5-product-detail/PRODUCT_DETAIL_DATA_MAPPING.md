# Product Detail Data Mapping

- Price: `amount_minor` + 3-letter ISO `currency` formatted via `formatMinorPrice()`.
- Discounts: `getDiscountPercentage()` computes a discount only when `original_amount_minor > amount_minor > 0`.
- Availability: `availabilityMessage()` & `canPurchase()` (`mobile/src/features/product-detail/utils/availability.ts`) allow purchase only for `in_stock` and `low_stock`.
