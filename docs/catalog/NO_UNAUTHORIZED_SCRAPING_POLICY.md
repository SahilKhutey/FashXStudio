# Policy on Unauthorized Web Scraping & Intellectual Property

## 1. Zero-Tolerance Unauthorized Scraping Rule

> **FashXStudio strictly prohibits unauthorized web scraping, screen extraction, credential spoofing, or automated harvesting of product catalogs without written authorization.**

This policy is core to FashXStudio's legal and ethical operational framework. Public accessibility of a website or product page does not convey permission to:
1. Harvest or ingest product descriptions, pricing, and variant details.
2. Store, reproduce, or mirror merchant product photographs.
3. Pass merchant images into computer vision, garment segmentation, or virtual try-on models.
4. Generate commercial affiliate links without merchant approval.

## 2. Invariants Enforced in Code

1. **Authorization Guard Preflight**: Every ingestion pipeline step executes `CatalogAuthorizationGuard.guard_product_read(source_id)` and `guard_product_store(source_id)` before any network payload is processed.
2. **Explicit Evidence Requirement**: A source cannot transition to `ACTIVE` without a verified `CatalogAuthorizationEvidence` record (e.g. signed bilateral contract or explicit API licensing agreement).
3. **No Unlicensed AI Processing**: Virtual Try-On (`VTO_PROCESS`) and Image Understanding (`IMAGE_AI_PROCESS`) permissions are distinct from display rights and must never be inferred.
4. **Mock Classification**: Any retailer integration lacking a bilateral contract (`AmazonAdapter`, `MyntraAdapter`, `FlipkartAdapter`) is permanently classified as `FIXTURE_ONLY` / `IntegrationStatus.MOCK`.
