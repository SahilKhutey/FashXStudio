# FashXStudio VTO — Phase 1: Source Integration

## Objective
Connect one authorized apparel source to the existing FashXStudio catalog pipeline so eligible garments can be selected by the VTO workflow.

## Existing modules reused
- `backend/fashx/catalog/acquisition/contract.py`
- `backend/fashx/catalog/acquisition/adapters/partner_feed.py`
- `backend/fashx/catalog/acquisition/pipeline.py`
- `backend/fashx/catalog/acquisition/image_validator.py`
- `backend/fashx/catalog/acquisition/normalizer.py`
- `backend/fashx/catalog/acquisition/sync_service.py`
- `scripts/catalog/validate_products_csv.py`
- `scripts/catalog/sync_sources.py`
- `scripts/catalog/clear_source.py`

## Feed configuration
Environment variables:
- `FASHX_PARTNER_FEED_SLUG`
- `FASHX_PARTNER_FEED_NAME`
- `FASHX_PARTNER_FEED_CSV`

The source slug must match an existing `CatalogSource` record.

## Required source clearance
Before a source can be enabled for production, verify written permission for:
1. Product metadata display.
2. Product image display.
3. Server-side AI image processing and virtual try-on.
4. Private image mirroring and storage, if images will be used for VTO.
5. Product data refresh and takedown procedures.

Do not treat a source's name, a feed URL, or a CSV flag as proof of permission.

## Data contract
Each feed item must include a stable source product ID, title, supported category, positive INR price, HTTPS product URL, and availability information.

For try-on, the image must also pass:
- source clearance and display rights
- source-level try-on rights
- item-level image and try-on permission
- required image storage policy
- safe URL and byte-level image validation
- canonical catalog eligibility

## Operational procedure
1. Obtain the partner's authorized feed.
2. Validate the CSV before ingestion.
3. Run adapter and acquisition unit tests.
4. Execute a dry-run and inspect all rejection reasons.
5. Verify source status and permissions in the target database.
6. Apply ingestion only after approval.
7. Verify the resulting canonical garment, offer, image provenance, and try-on eligibility.
8. Record the run output and source evidence.

## Prohibited shortcuts
- No scraping of retailer product pages.
- No bypassing the source approval guard.
- No production use of synthetic seed records as real products.
- No assumption that an image URL implies image rights.
- No automatic clearance based only on a CSV value.
- No hotlink-only image source for VTO where private mirroring is required.

## Exit criteria
- One source has verified written permission and operational access.
- Source slug and feed configuration match the registered source.
- CSV validation and adapter tests pass.
- Dry-run rejection reasons are understood.
- Repeated ingestion does not create duplicate product records.
- At least one real garment is stored with valid provenance and verified VTO eligibility.
- A reproducible evidence record is saved.

A local fixture or passing unit test alone does not satisfy the real-source or production-readiness criteria.
