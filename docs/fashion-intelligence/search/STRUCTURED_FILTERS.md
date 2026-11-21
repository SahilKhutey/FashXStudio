# Structured Filters Specification

## 1. Overview
Structured filters allow shoppers to narrow down catalog listings using exact, verified parameters. Filters are evaluated as strict constraints (`WHERE` clauses in SQL) rather than fuzzy ranking factors.

---

## 2. Supported Filters

### 2.1 Category Filtering (`category_id`)
- Evaluates against Phase 06.1 taxonomy category IDs.
- Hierarchy support: Selecting a parent category (e.g. `apparel/tops`) automatically matches products classified under any of its descendant subcategories (e.g. `t_shirt`, `shirt`, `blouse`).
- Quarantined or unclassified products are never included.

### 2.2 Brand Filtering (`brand_id`)
- Normalized brand entities.
- Brand aliases resolve to the single canonical brand ID.
- Brand is strictly decoupled from merchant identity.

### 2.3 Price and Currency Filtering (`min_price`, `max_price`, `currency`)
- Evaluates against the **active merchant offer** (`merchant_offers.price_amount`).
- Currency verification: Queries specify an ISO 4217 3-letter currency code (default: `INR`). Mismatched currencies are never directly compared.
- Invariants: `min_price >= 0`, `max_price >= 0`, and `min_price <= max_price`.

### 2.4 Color Filtering (`color_id`)
- Uses Phase 06.1 controlled color taxonomy.
- Supports multi-color items: A product with primary `navy_blue` and secondary `white` matches queries filtering on either color.

### 2.5 Occasion Filtering (`occasion_id`)
- Matches against verified occasion attributes extracted in Phase 06.2 (`casual`, `office`, `festive`, `wedding`, `party`).
- Low-confidence or unapproved occasion inferences are excluded from hard filtering.
