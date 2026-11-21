# Catalog Data Permission Policy

**Workstream**: 5.1.5 — Catalog Textual & Structured Data Permissions  
**Status**: Active  
**Enforcement Engine**: `backend/fashx/catalog/authorization/`

---

## 1. Objective and Core Invariant
Catalog data consists of product titles, descriptions, categories, subcategories, brand attributions, attributes (e.g. fabric, color, cut), sizing charts, pricing, and stock status.

**Core Invariant**:
> Reading or indexing product metadata does not grant permission to store that metadata indefinitely, display it publicly to shoppers, or redistribute it to external parties. Each operation requires explicit contractual authorization.

---

## 2. Granular Permission Scopes

### 2.1 `PRODUCT_DATA_READ`
- **Definition**: Authority to fetch raw product listings, metadata, attributes, and pricing from the merchant's integration endpoint.
- **Allowed Operations**:
  - Executing API calls to merchant product endpoints.
  - Downloading product feed files.
  - Parsing product schemas into staging memory.
- **Prohibited Operations**:
  - Writing raw data into long-term customer-facing database tables.
  - Rendering product titles/descriptions in shopper search or feeds.

### 2.2 `PRODUCT_DATA_STORE`
- **Definition**: Authority to persist normalized product records into FashXStudio internal databases (`merchant_products`, `offers`, `canonical_garments`).
- **Allowed Operations**:
  - Database inserts, updates, and indexing.
  - Generating internal semantic embeddings and classification tags.
  - Computing internal inventory and deduplication indices.
- **Prohibited Operations**:
  - Public display if `PRODUCT_DISPLAY` is absent.

### 2.3 `PRODUCT_DISPLAY`
- **Definition**: Authority to publish product information to shoppers on the mobile application, web, and search feeds.
- **Allowed Operations**:
  - Displaying product title, description, price, and merchant brand in shopper discovery feeds.
  - Displaying product details in recommendation cards and styling builders.
- **Prohibited Operations**:
  - Processing product images for virtual try-on or generative AI without specific AI permission.

---

## 3. Scope Constraints & Enforcements
Each permission record in `catalog_source_permissions` can restrict data permissions via:
- `scope_categories`: JSON array of allowed categories (e.g., `["apparel", "footwear"]`). If a product belongs to `jewelry` and the source scope is limited to `apparel`, the evaluation engine returns `DENY_CATEGORY_OUT_OF_SCOPE`.
- `scope_markets`: JSON array of sovereign market codes (e.g., `["IN"]`). Products intended for other markets are rejected with `DENY_MARKET_OUT_OF_SCOPE`.
- `storage_limit_days`: If contractual data retention requires purging after $N$ days, the background worker automatically schedules data erasure.
