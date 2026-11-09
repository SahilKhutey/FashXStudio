# RC13: Catalog Operations & Commerce Boundary Validation

## 1. Catalog Quality Invariants
- **Schema Completeness**: All active catalog garments must supply title, brand, category, gender, color, verified retailer URL, and verified image assets.
- **Visual Embeddings**: Garments in the active pool must have valid 512-dim visual embeddings for semantic vector matching.
- **Stock & Link Freshness**:
  - Validated by [`scripts/rc12/catalog_health.py`](file:///c:/Users/ASUS/Documents/FashXStudio/scripts/rc12/catalog_health.py).
  - Out-of-stock items filtered from recommendation feeds.
  - Zero broken image links (HTTP 200 required).

## 2. Commerce Boundary & Affiliate Handoff
- **Explicit Boundary**: FashXStudio operates exclusively as a discovery and virtual try-on technology layer.
- **No Native Checkout**: The application does not collect payments, store credit card details, process orders, or handle shipping logistics.
- **Redirect Attribution**: User clicks on "Buy at Retailer" redirect out to the merchant's store with UTM parameters and affiliate tags (`utm_source=fashx&utm_campaign=vto_discovery`).
