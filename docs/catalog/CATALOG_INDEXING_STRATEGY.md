# Catalog Indexing Strategy

## 1. Candidate Query Patterns
1. Product lookup by source identity: `(source_id, source_product_id)`.
2. Active merchant offers: `(merchant_id, status)`.
3. Garment offers: `(garment_id)`.
4. Price range and currency filtering: `(currency, price_minor)`.
5. Availability queries: `(availability)`.
6. Merchant sources: `(merchant_id, source_status)`.
7. Category and brand discovery: `(category, brand_id)`.
8. Offer size lookup: `(size_definition_id, availability)`.
9. Offer price history: `(merchant_offer_id, observed_at)`.
10. Attribute provenance: `(entity_type, entity_id, attribute_name)`.

## 2. Production Index Implementation
- `uq_product_source_pid` on `merchant_products (source_id, source_product_id)`
- `ix_merchant_offers_merchant_status` on `merchant_offers (merchant_id, status)`
- `ix_merchant_offers_price_currency` on `merchant_offers (currency, price_minor)`
- `ix_merchant_offers_availability` on `merchant_offers (availability)`
- `ix_merchant_offers_merchant_product` on `merchant_offers (merchant_product_id)`
- `ix_catalog_sources_merchant_status` on `catalog_sources (merchant_id, source_status)`
- `ix_garments_category_brand` on `canonical_garments (category, brand_id)`
- `ix_garments_brand` on `canonical_garments (brand_id)`
- `ix_offer_sizes_size_availability` on `merchant_offer_sizes (size_definition_id, availability)`
- `ix_price_history_offer_observed` on `merchant_offer_price_history (merchant_offer_id, observed_at)`
- `ix_provenance_entity_attr` on `catalog_provenance_records (entity_type, entity_id, attribute_name)`
