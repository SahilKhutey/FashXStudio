# P5 — Automated Catalog Acquisition and Ingestion Architecture
Project: FashXStudio  
Milestone: P5 Final  
Status: Implemented & Tested

## Purpose and Scope
Establish FashXStudio's automated, extensible, permission-aware catalog acquisition and ingestion architecture. The architecture makes the apparel catalog a continuously updated service powering discovery, personalization, product comparisons, and virtual try-on, eliminating manual garment entry from the production workflow while retaining fixtures for automated testing.

## Architectural Layers and Deliverables

### 1. Source Adapter Contract & Registry (`backend/fashx/catalog/acquisition/`)
- **`SourceProduct` & `AcquisitionBatch` DTOs (`contract.py`)**: Immutable, type-safe data transfer objects standardizing products fetched across stores.
- **`CatalogSourceAdapter` Protocol**: Common interface requiring `source_slug` and `fetch_batch(cursor, limit) -> AcquisitionBatch`.
- **`AdapterRegistry` (`registry.py`)**: Thread-safe registry and configuration manager holding source-specific RPS limits, circuit breaker settings, timeouts, and refresh policies.
- **Store Adapters (`adapters/`)**:
  - `BaseSourceAdapter`: Implements sliding-window rate limiting, exponential backoff, and circuit breaker protection (CLOSED -> OPEN -> HALF_OPEN).
  - `AmazonAdapter`: Adapter for Amazon product feeds and Product Advertising API.
  - `MyntraAdapter`: Adapter for Myntra partner feeds and API integrations.
  - `FlipkartAdapter`: Adapter for Flipkart partner feeds and API integrations.
  - `PartnerFeedAdapter`: Reference adapter supporting local/remote CSV and JSON data feeds.

### 2. Normalization Pipeline (`normalizer.py`)
- **Category Taxonomy**: Normalizes external retail categories and keywords to canonical values (`tops`, `bottoms`, `dresses`, `outerwear`) and subcategories (`shirt`, `tshirt`, `jeans`, `trousers`, `dress`, `jacket`, etc.).
- **Price & Currency**: Enforces integer paise minor units (`price_minor > 0`) and INR currency.
- **Brand Extraction**: Cleans whitespace, title-cases, and strips corporate suffixes (`Pvt Ltd`, `LLC`, `Inc`).
- **Sizes**: Normalizes alpha sizes (`XS`, `S`, `M`, `L`, `XL`, etc.) and waist sizes (`28`, `30`, `32`, etc.).
- **URL Sanitization**: Strips tracking and marketing parameters (`utm_*`, `ref*`, `gclid`, `fbclid`, `tag`) while preserving product paths and identifiers.

### 3. Safe Image Validation & SSRF Protection (`image_validator.py`)
- **Scheme Check**: Requires HTTPS.
- **SSRF Defense**: Resolves hostname and blocks loopback, private IPv4/IPv6 ranges (`127.0.0.0/8`, `10.0.0.0/8`, `172.16.0.0/12`, `192.168.0.0/16`, `169.254.0.0/16`, `::1`), and link-local addresses.
- **Extension & MIME**: Restricts to approved image types (`.jpg`, `.jpeg`, `.png`, `.webp`).
- **Independent Eligibility**:
  - *Listing Discovery*: Valid product schema and cleared source status.
  - *Image Display*: Source display rights + approved image rights (`owned`, `licensed`, `partner_authorized`).
  - *Virtual Try-On*: Source tryon rights + `image_policy="mirror"` + item tryon permission.

### 4. Idempotent Ingestion & Deduplication Pipeline (`pipeline.py`)
- **Two Levels of Identity**:
  - Source Product Identity: `(source_id, source_product_id)` uniquely identifies a listing within a source.
  - Canonical Garment Identity: links listings representing the same garment across sellers.
- **Change Detection**: Detects price, stock, size, and metadata updates. Updates existing `MerchantProduct`, `MerchantOffer`, and `CanonicalGarment` records idempotently without duplicate insertions.
- **No Self-Granted Clearance**: Unapproved sources cannot grant themselves feed approval or permissions.
- **Audit Logging**: Persists `IngestRun` records with execution timestamps, counts (inserted, updated, unchanged, rejected), and structured rejection reasons.

### 5. Scheduled Sync & Stale Reconciliation (`sync_service.py` & `scripts/catalog/sync_sources.py`)
- **`CatalogSyncService`**: Orchestrates scheduled batch acquisition across all registered adapters with failure isolation (one source failing does not block other sources).
- **Stale Offer Reconciliation (`reconcile_stale_offers`)**: Automatically detects offers unrefreshed past a configured threshold (default 48h) and marks them `in_stock = False`, reconciling `CanonicalGarment.in_stock` accordingly.
- **CLI Sync Tool (`scripts/catalog/sync_sources.py`)**: Command-line interface supporting `--source <slug>`, `--all`, `--reconcile-stale`, `--dry-run`, and `--apply`.

## Verification Results

| Check / Test Suite | Command | Result |
|---|---|---|
| Docs Lint | `python scripts/docs_lint.py` | `docs lint ok` |
| Python Ruff Linter | `ruff check .` | `All checks passed!` |
| Python Mypy Type Checker | `mypy .` | `Success: no issues found in 1011 source files` |
| Acquisition Contract & Registry Tests | `python -m pytest tests/unit/test_catalog_acquisition_contract.py -v` | 3 passed |
| Catalog Normalizer Tests | `python -m pytest tests/unit/test_catalog_normalizer.py -v` | 6 passed |
| Safe Image & SSRF Validator Tests | `python -m pytest tests/unit/test_image_ssrf_validator.py -v` | 3 passed |
| Acquisition Pipeline & Idempotency Tests | `python -m pytest tests/unit/test_acquisition_pipeline.py -v` | 3 passed |
| Store Adapters & Circuit Breaker Tests | `python -m pytest tests/unit/test_source_adapters.py -v` | 3 passed |
| Sync Service & Stale Reconciliation Tests | `python -m pytest tests/unit/test_sync_and_stale_reconciliation.py -v` | 2 passed |
| Complete Catalog Test Suite (Unit & Integration) | `python -m pytest tests/unit/test_*catalog* tests/unit/test_*acquisition* tests/unit/test_image_ssrf_validator.py tests/unit/test_source_adapters.py tests/unit/test_sync_and_stale_reconciliation.py tests/integration/test_catalog_ingestion_parity.py -v` | 42 passed in 14.11s |
| Sync Sources CLI Dry-Run (All Adapters) | `python scripts/catalog/sync_sources.py --all --dry-run --db-url sqlite+aiosqlite:///:memory:` | 4 sources synced (Amazon, Flipkart, Myntra, Manual-Demo): 14 inserted, 0 rejected |
| Stale Reconciliation CLI (SQLite) | `python scripts/catalog/sync_sources.py --reconcile-stale --max-age-hours 48 --apply --db-url sqlite+aiosqlite:///:memory:` | Executed cleanly, 0 stale offers detected |
| Mobile ESLint, TypeScript & Jest Suites | `cd mobile; npx eslint . --max-warnings 0; npx tsc --noEmit; npx jest --ci; cd ..` | 12 passed, 12 total (97 tests) |
| Android Expo Export | `cd mobile; npx expo export --platform android; cd ..` | 1591 modules bundled, exported to dist |

## P5 Checklist Execution Summary

- [x] **P5.1**: Audit catalog schema, migrations, API routes and source lifecycle.
- [x] **P5.2**: Remove implicit source approval and enforce strict source status checks.
- [x] **P5.3**: Define the adapter contract (`CatalogSourceAdapter`), DTOs, and source registry.
- [x] **P5.4**: Implement first authorized adapters (Partner Feed, Amazon, Myntra, Flipkart) and common normalization pipeline.
- [x] **P5.5**: Make product and offer ingestion idempotent with change tracking and `IngestRun` auditing.
- [x] **P5.6**: Implement safe image validation, SSRF protection, MIME verification, and independent permissions.
- [x] **P5.7**: Integrate quality checks and source-specific stale-data reconciliation (`reconcile_stale_offers`).
- [x] **P5.8**: Add scheduled synchronization service (`CatalogSyncService`) and CLI sync tool.
- [x] **P5.9**: Connect feed eligibility to the existing catalog API and mobile feed (`list_feed_candidates`).
- [x] **P5.10**: Run backend, integration, security, and static type checks.

## Known Blockers & Limitations (Rule 14)
- **Hosted PostgreSQL**: Backend tests were executed against SQLite in-memory; live PostgreSQL was unreachable locally (`[WinError 1225] The remote computer refused the network connection`) and remains unverified locally until CI run.
- **Live Commercial Store APIs**: Adapters for Amazon, Myntra, and Flipkart implement the full protocol with rate limiting and circuit breakers, tested against local authorized feeds; production API keys/credentials are not configured locally.
- **Physical Mobile Hardware**: Mobile validation completed via Jest tests, TypeScript type checking, and Expo Android static bundling; physical device test remains unverified.
