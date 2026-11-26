# 06 — Variant Availability Model

## 1. Separation of Size Data and Availability

A foundational rule of FashXStudio is that size definitions and stock availability are independent concepts:
- **Size Chart**: Defines what dimensions the merchant manufactures for each size label.
- **Variant Inventory**: Reports whether a specific SKU / variant (size, colour) is purchasable right now.

A size chart row does **NOT** indicate inventory. A shopper may see that "XL" exists in the merchant's size chart, while the variant selector indicates that "XL" is currently out of stock.

## 2. Inventory Snapshots (`inventory_snapshots`)

Variant inventory is tracked through point-in-time observations:
- `variant_id`: Merchant variant identifier.
- `size_label`: The size label associated with this variant.
- `colour_label`: Optional colour identifier.
- `sku`: Merchant SKU code.
- `availability_status`: One of `IN_STOCK`, `LOW_STOCK`, `OUT_OF_STOCK`, `PREORDER`, or `UNKNOWN`.
- `observed_at`: Exact timestamp when the stock status was verified.

## 3. Freshness Policy & Graceful Degradation

Inventory data is volatile. FashXStudio applies an automatic degradation policy:
- **Active Freshness (0 to 24 hours)**: The observed status is reported directly.
- **Stale (> 24 hours without sync)**:
  - If the last observed status was `IN_STOCK` or `LOW_STOCK`, it automatically degrades to `UNKNOWN`.
  - **Invariant**: The system **never** falsely claims an item is `OUT_OF_STOCK` solely because data is stale, nor does it falsely claim an item is `IN_STOCK` when synchronization has lapsed.
  - If the last observed status was `OUT_OF_STOCK`, it remains `OUT_OF_STOCK` until a positive stock sync occurs.
