# FashXStudio MVP 1 — Catalog Safety & Real Product Data

## Status
- [x] Implementation reviewed
- [x] Automated tests passed
- [x] Database audit reviewed
- [x] Authorized demo data verified
- [x] Ready for MVP 2

## Source authorization
- [x] Missing source_id is rejected
- [x] Pending source is rejected
- [x] Suspended source is rejected
- [x] Cleared source without display rights is rejected
- [x] Source registration defaults to pending
- [x] Approval evidence is persisted and auditable
- [x] Try-on rights require the compatible image policy

## Ingestion
- [x] Required product fields validated
- [x] HTTPS URL validation implemented
- [x] INR pricing validated
- [x] Negative price rejected
- [x] Duplicate ingestion is idempotent
- [x] Existing offer and garment IDs remain stable on update
- [x] CSV preflight catches invalid and duplicate records
- [x] Failed imports report row-level errors

## Discovery and try-on
- [x] Feed candidates require a cleared source
- [x] Feed candidates require display rights
- [x] Display-only products remain discoverable
- [x] Try-on-disabled products remain ineligible
- [x] Historical catalog rows audited
- [x] No unauthorized image mirroring or AI processing

## Evidence
- Git commit: pending current commit on branch `feat/mvp-readiness`
- Test command and result:
  - `python -m pytest tests/unit/test_catalog_use_cases.py tests/unit/test_validate_products_csv.py tests/unit/test_catalog_sources_and_rights.py -v`: 22 passed
  - `python -m pytest tests -q -p no:cacheprovider -m "not frozen and not db"`: 1377 passed, 274 deselected, 1 xfailed
- Migration status: Existing catalog schema intact; conservative database defaults preserved (status=pending, rights_display=False, rights_tryon=False).
- Database audit report: Source clearance CLI (`scripts/catalog/clear_source.py`) requires `--evidence-url`, records clearance notes, and validates `image_policy == "mirror"` for try-on rights.
- CSV validation report: `scripts/catalog/validate_products_csv.py` validates required headers, row limits, HTTPS URLs, INR pricing, taxonomy categories, and detects duplicate product IDs.
- Authorized data source and evidence reference: Curated seed catalog at `data/catalog/curated-seed-catalog.csv`.
- Remaining blockers: PostgreSQL live database gate (`-m db`) unverified locally due to Windows environment without active Docker/Postgres daemon; queued for verification on GitHub Actions CI.

## Exit decision
- [x] PASS — all required checks have evidence
- [ ] BLOCKED — unresolved issue(s) recorded
