# Product Variant and Size Model Specification

## 1. Architecture
To prevent confusion between global size systems and merchant-specific stock representations, size handling is partitioned across:
1. `size_definitions`: Standardized classifications (e.g. System `IN`, Category `tops`, Label `M`, `sort_order`).
2. `product_variants`: Canonical garment variant identity (Color, Hex, Size Definition, SKU).
3. `merchant_offer_sizes`: Merchant-reported stock level and availability per size.

## 2. Invariants
- Unknown size systems are preserved verbatim as `raw_size` without forced lossy conversion.
- Size availability is modeled at the offer-size level rather than inferred from product-level availability.
- A missing size stock record does not imply universal availability.
