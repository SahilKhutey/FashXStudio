# Catalog Data Model Specification

## 1. Architectural Principles
1. **Canonical Garment != Merchant Product**: A canonical garment represents the underlying product identity; merchant listings represent individual commercial offers.
2. **Merchant != Brand**: A merchant sells products from many brands; a brand can be sold by many merchants.
3. **Product != Variant**: Size and color variants are never merged into an indistinguishable single record.
4. **Current Price != Price History**: Current price is optimized for lookup and filtering; historical observations are append-only in `merchant_offer_price_history`.
5. **Last Seen != Last Verified**: A record can be observed in a source feed without its price or availability having been independently verified.
6. **Inactive != Deleted**: Temporarily out-of-stock products retain their full historical records.

## 2. Entity Hierarchy
```
MERCHANT
  |
  +---- CATALOG_SOURCE
  |        |
  |        +---- INGEST_RUN
  |        |
  |        +---- MERCHANT_PRODUCT
  |                   |
  |                   +---- MERCHANT_OFFER
  |                   |         |
  |                   |         +---- OFFER_PRICE_HISTORY
  |                   |         |
  |                   |         +---- MERCHANT_OFFER_SIZE
  |                   |
  |                   +---- GARMENT_IMAGE
  |                             |
  |                             +---- CATALOG_IMAGE_ASSET
  |
  +---- MERCHANT_OFFER

BRAND
  |
  +---- CANONICAL_GARMENT
              |
              +---- MERCHANT_PRODUCT
              |
              +---- PRODUCT_VARIANT
```

## 3. Entity Separation
| Field | Canonical Garment | Merchant Offer |
|---|---|---|
| Brand | `brand_id` (FK) | None |
| Title | Canonical `display_name` | Source `title` on `MerchantProduct` |
| Category | Standardized `category` | Source category mapping |
| Price | None (commercial attribute) | `price_minor`, `currency` |
| Availability | Stock indicator | `status`, `availability`, `in_stock` |
| Product URL | None | `url` |
| Sizes | Available sizes summary | `MerchantOfferSize` breakdown |
