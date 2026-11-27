# 05 — Merchant-Specific Sizing & Offer Isolation

## Strict Isolation Invariants

Every recommendation resolves and records exact provenance:
- `merchant_id`
- `merchant_product_id`
- `merchant_offer_id`
- `product_id` (`CanonicalGarment.id`)
- `variant_id`
- `size_chart_id` & `size_chart_revision`
- `source_id`, `source_revision`, & `source_permission_revision`
- `taxonomy_version`, `category_policy_version`, `fit_algorithm_version`

If a `ProductSizeChartResponse` carries a `merchant_id` or `merchant_product_id` differing from the resolved offer, `evaluate_recommendation` detects `merchant_isolated=False` and returns `CONFLICTING_DATA` without issuing a size label. Merchant labels (`M`, `L`, `40`) are never translated across merchants.
