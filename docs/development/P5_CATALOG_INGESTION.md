# P5 — Real Garment Catalog and Ingestion Pipeline
Project: FashXStudio  
Milestone: P5  
Status: Implemented & Tested

## Purpose and Scope
Establish FashXStudio's canonical garment catalog and ingestion pipeline. The milestone resolves product blockers around absent product data and unvalidated catalog inputs by providing:
1. A canonical apparel seed dataset of real, legally compliant garments across multiple categories.
2. A fail-fast CSV validator enforcing structural schema, category taxonomies, positive INR prices in paise, secure HTTPS image URLs, and explicit legal rights.
3. A hardened ingestion use case preventing unauthorized sources from self-granting clearance or try-on permissions, persisting deduplicated `GarmentImage` records, and independently enforcing try-on eligibility.
4. A hardened `CatalogQualityGate` failing closed on empty batches and auditing individual item eligibility.
5. An ingestion CLI importer supporting both dry-run simulation and production apply modes.

## Architecture and Deliverables

### 1. Canonical Apparel Seed Dataset (`data/catalog/catalog_seed.csv`)
- Contains 10 curated apparel items spanning `tops`, `bottoms`, `dresses`, and `outerwear`.
- Prices denominated in positive integer paise (`price_minor > 0`) with currency `INR`.
- Valid HTTPS product and image URLs with strict prevention of private/localhost hosts.
- Explicit image rights (`owned`) and item-level try-on permissions (`true`/`false`).

### 2. Pre-Ingestion CSV Validator (`scripts/catalog/validate_catalog_csv.py`)
- **Required Columns**: Enforces exact column presence (`source_slug`, `source_product_id`, `title`, `category`, `price_minor`, `currency`, `in_stock`, `product_url`, etc.).
- **Identifier Deduplication**: Rejects duplicate `source_product_id` values within the batch.
- **Taxonomy Validation**: Enforces standard categories (`tops`, `bottoms`, `dresses`, `outerwear`, etc.).
- **Price Integrity**: Ensures prices are positive integers in paise (`price_minor > 0`) and currency is `INR`.
- **URL Security**: Verifies HTTPS scheme and blocks `localhost`, `127.0.0.1`, and private IP addresses.
- **Rights Verification**: Enforces valid `image_rights` (`owned`, `licensed`, `partner_authorized`).

### 3. Hardened Ingestion Use Case (`backend/fashx/catalog/application/ingest_product.py`)
- **No Self-Granted Clearance**: Fallback source auto-creation sets `status="pending_approval"`, `rights_display=False`, and `rights_tryon=False`. Missing sources can no longer self-grant feed clearance.
- **Strict Source Resolution**: Commands specifying explicit `source_id` reject non-existent sources with `EntityNotFoundError`.
- **Image Persistence & Deduplication**: Persists `GarmentImage` records keyed by `content_hash` (SHA-256) via `GarmentImageRepository`. Re-ingesting identical image URLs for a garment reuses the existing record without duplicate key violations.
- **Independent Try-On Enforcement**: Try-on eligibility requires BOTH the source to have `rights_tryon=True` AND the product command to specify `tryon_rights=True`.

### 4. Catalog Quality Gate (`backend/fashx/catalog/quality/quality_gate.py`)
- **Fail-Closed Empty Batch**: Empty batches return `passed_gate=False` and `completeness_score=0.0`.
- **Taxonomies Enforced**: Includes standard fashion taxonomies for silhouettes, dominant colors, and image rights.
- **Individual Item Eligibility (`is_item_eligible`)**: Evaluates category validity, positive pricing, in-stock state, source clearance, HTTPS URL safety, and rights independently, preventing batch averages from masking bad records.

### 5. Ingestion CLI Importer (`scripts/catalog/import_catalog_csv.py`)
- Supports `--dry-run` (simulates entire domain execution and rolls back transaction) and `--apply` (commits database writes).
- Configurable database connection via `--db-url` (supporting SQLite in-memory for testing and offline development).
- Generates structured import summaries including row counts, inserted/updated counts, rejection reasons, and quality gate scores.

## Verification Results

| Check / Test Suite | Command | Result |
|---|---|---|
| Docs Lint | `python scripts/docs_lint.py` | `docs lint ok` |
| Python Ruff Linter | `ruff check .` | `All checks passed!` |
| Python Mypy Type Checker | `mypy .` | `Success: no issues found in 991 source files` |
| P5 Unit Tests (CSV Validator & Ingestion) | `python -m pytest tests/unit/test_validate_catalog_csv.py tests/unit/test_catalog_quality_gate.py tests/unit/test_catalog_ingestion_hardening.py -v` | 17 passed in 4.04s |
| Catalog Integration & Parity Tests | `python -m pytest tests/unit/test_catalog_use_cases.py tests/integration/test_catalog_ingestion_parity.py -v` | 5 passed in 2.22s |
| CSV Validator CLI | `python scripts/catalog/validate_catalog_csv.py data/catalog/catalog_seed.csv` | `VALIDATION PASSED` |
| Importer CLI Dry-Run (SQLite) | `python scripts/catalog/import_catalog_csv.py data/catalog/catalog_seed.csv --dry-run --db-url sqlite+aiosqlite:///:memory: --auto-register-source` | 10 processed, 10 inserted, 0 rejected, Quality Gate: PASSED (100.0%) |
| Importer CLI Apply (SQLite) | `python scripts/catalog/import_catalog_csv.py data/catalog/catalog_seed.csv --apply --db-url sqlite+aiosqlite:///:memory: --auto-register-source` | 10 processed, 10 inserted, 0 rejected, Quality Gate: PASSED (100.0%) |
| Mobile ESLint, TypeScript & Jest Suites | `cd mobile; npx eslint . --max-warnings 0; npx tsc --noEmit; npx jest --ci; cd ..` | 12 passed, 12 total (97 tests) |
| Android Expo Export | `cd mobile; npx expo export --platform android; cd ..` | 1591 modules bundled, exported to dist |

## Milestone Completion Status

| Capability | Implemented | Unit Tested | Verified End-to-End |
|---|---|---|---|
| Canonical Apparel Seed CSV | Yes | Yes (schema & values) | Validated via CLI |
| Structural CSV Validator | Yes | Yes (9 test cases) | Verified on seed & fixtures |
| Hardened Ingestion Use Case | Yes | Yes (4 test cases) | Verified via UnitOfWork & CLI |
| SHA-256 Image Deduplication | Yes | Yes | Verified in SQLite / UnitOfWork |
| Independent Try-On Rights Guard | Yes | Yes | Verified in UnitOfWork |
| Catalog Quality Gate (Fail-Closed) | Yes | Yes (4 test cases) | Verified on audit batches |
| Pipeline CLI Importer (`--dry-run`, `--apply`) | Yes | Yes | Verified on seed dataset |
| Real Brand External Feed Sync | Pending | Pending | Blocked (no live commercial partner feeds) |

## Known Blockers & Limitations (Rule 14)
- **Hosted PostgreSQL**: Backend tests were executed against SQLite in-memory; live PostgreSQL was unreachable locally (`[WinError 1225] The remote computer refused the network connection`) and remains unverified locally until CI run.
- **Commercial Brand Partner Feeds**: Real catalog data is provided via the local authorized seed dataset (`data/catalog/catalog_seed.csv`); live automated scraping or external affiliate ingestion pipelines are excluded by design.
- **Physical Mobile Hardware**: Mobile verification completed via Jest tests, TypeScript type checking, and Expo Android static bundling; physical device test remains unverified.
