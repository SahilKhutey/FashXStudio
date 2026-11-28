# 05 — Price and Currency Display

- `mobile/src/features/catalog/components/PriceDisplay.tsx` (`formatCurrencyPrice`) formats decimal amounts with explicit 3-letter ISO currency via `Intl.NumberFormat` and displays `"Price unavailable"` when null or invalid.
- `priceToMinorUnits` converts backend decimal amounts safely for `ProductCard`.
