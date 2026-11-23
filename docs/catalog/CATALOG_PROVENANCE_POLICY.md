# Catalog Provenance Policy

## 1. Principles
Every source-managed attribute change in FashXStudio catalog retains:
- `source_id`: The authorized source supplying the datum.
- `merchant_id`: Commercial owner.
- `ingest_run_id`: Exact batch execution run.
- `recorded_at`: System UTC timestamp.
- `confidence`: Attribution confidence score.

## 2. Multi-Source Attribute Preservation
When multiple sources provide conflicting attributes (e.g. conflicting titles or categorizations):
- Competing observations are preserved in `catalog_provenance_records`.
- Attributes are never silently overwritten without historical attribution.
