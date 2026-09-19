# AI Fashion Assistant — Production Build Foundation 9

## Catalog Runtime Foundation

Foundation 9 turns the catalog contract into the first production-shaped MVP catalog runtime.

### Scope

- Canonical garment identity is separate from merchant product identity.
- A merchant product now points to its canonical garment through `canonical_garment_id`.
- Re-importing the same merchant/source product updates the existing record instead of creating a second garment.
- Canonical garments have a stable `display_name` for feed/read-model use.
- Merchant offers are unique per `(merchant_id, source_product_id)`.
- Curated catalog imports can include image metadata and deterministic content hashes.
- Catalog search returns feed-ready summaries including lowest in-stock price and a primary image key.
- Catalog detail returns garment, images, offers and latest enrichment when available.

## MVP import path

```text
Curated JSON
    ↓
Brand / Merchant normalization
    ↓
MerchantProduct upsert
    ↓
CanonicalGarment creation / reuse
    ↓
MerchantOffer upsert
    ↓
GarmentImage upsert
    ↓
Feed-ready catalog
```

The import mechanism is intentionally a script rather than the future multi-source worker framework. It uses the same application service and repository invariants as the runtime API.

Example:

```bash
python -m scripts.catalog_import.import_catalog \
  --file scripts/catalog_import/catalog_fixture.json
```

## Important invariant

Foundation 9 intentionally removes the earlier category-based canonicalization behavior. Two shirts from the same brand are not the same physical garment merely because they share category/subcategory. In the MVP, each merchant source product receives its own canonical garment unless an explicit future deduplication process merges it.

## Migration

`0008_catalog_runtime` adds:

- `merchant_products.canonical_garment_id`
- `canonical_garments.display_name`
- unique merchant/source offer constraint
- catalog search indexes

## Deferred

- Affiliate-network ingestion workers
- VLM enrichment execution
- OCR execution
- image download/transcoding to R2
- perceptual deduplication across merchants
- vector similarity retrieval

Those belong to later catalog/enrichment phases.
