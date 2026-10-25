# P5 — Automated Catalog Acquisition and Ingestion Architecture
Project: FashXStudio  
Milestone: P5 Final (P5.0 – P5.10)  
Status: Implemented & Tested

## Purpose and Scope
Establish FashXStudio's automated, extensible, permission-aware catalog acquisition and ingestion architecture. The architecture makes the apparel catalog a continuously updated service powering discovery, personalization, product comparisons, and virtual try-on, eliminating manual garment entry from the production workflow while retaining fixtures for automated testing.

## Architectural Layers and Deliverables (P5.0 – P5.10)

### 1. Source Adapter Contract & Registry (`backend/fashx/catalog/acquisition/`) [P5.0 – P5.2]
- **`SourceProduct` & `AcquisitionBatch` DTOs (`contract.py`)**: Immutable, type-safe data transfer objects standardizing products fetched across stores.
- **`CatalogSourceAdapter` Protocol**: Common interface requiring `source_slug` and `fetch_batch(cursor, limit) -> AcquisitionBatch`.
- **`AdapterRegistry` (`registry.py`)**: Thread-safe registry and configuration manager holding source-specific RPS limits, circuit breaker settings, timeouts, and refresh policies.
- **Store Adapters (`adapters/`)**:
  - `BaseSourceAdapter`: Implements sliding-window rate limiting, exponential backoff, and circuit breaker protection (CLOSED -> OPEN -> HALF_OPEN).
  - `AmazonAdapter`: Adapter for Amazon product feeds and Product Advertising API.
  - `MyntraAdapter`: Adapter for Myntra partner feeds and API integrations.
  - `FlipkartAdapter`: Adapter for Flipkart partner feeds and API integrations.
  - `PartnerFeedAdapter`: Reference adapter supporting local/remote CSV and JSON data feeds.
- **Fail-Closed Approval Lifecycle (`backend/fashx/catalog/acquisition/pipeline.py` & `application/ingest_product.py`)**:
  - In automated acquisition (`AcquisitionPipeline`): Unregistered or unapproved (`status != "cleared"`) sources are strictly rejected and refused ingestion.
  - In direct ingestion (`IngestMerchantProductUseCase`): Unregistered `source_id` raises `EntityNotFoundError`. When `source_id` is omitted, fallback sources default to `status="pending_approval"`, `rights_display=False`, and `rights_tryon=False`, ensuring unapproved sources never self-grant feed or try-on clearance.

### 2. Product Normalization & Validation (`normalizer.py`) [P5.3]
- **Category Taxonomy**: Normalizes external retail categories and keywords to canonical values (`tops`, `bottoms`, `dresses`, `outerwear`) and subcategories (`shirt`, `tshirt`, `jeans`, `trousers`, `dress`, `jacket`, etc.).
- **Price & Currency**: Enforces integer paise minor units (`price_minor > 0`) and INR currency.
- **Brand Extraction**: Cleans whitespace, title-cases, and strips corporate suffixes (`Pvt Ltd`, `LLC`, `Inc`).
- **Sizes**: Normalizes alpha sizes (`XS`, `S`, `M`, `L`, `XL`, etc.) and waist sizes (`28`, `30`, `32`, etc.).
- **URL Sanitization**: Strips tracking and marketing parameters (`utm_*`, `ref*`, `gclid`, `fbclid`, `tag`) while preserving product paths and identifiers.

### 3. Idempotent Ingestion & Change Detection Pipeline (`pipeline.py`) [P5.4]
- **Dual Identity Model**:
  - Source Product Identity: `(source_id, source_product_id)` uniquely identifies a listing within a source.
  - Canonical Garment Identity: links listings representing the same garment across sellers.
- **Change Detection**: Detects price, stock, size, and metadata updates. Updates existing `MerchantProduct`, `MerchantOffer`, and `CanonicalGarment` records idempotently without duplicate insertions.
- **Audit Logging**: Persists `IngestRun` records with execution timestamps, counts (inserted, updated, unchanged, rejected), and structured rejection reasons.

### 4. Image Acquisition, Byte Validation & SSRF Protection (`images/` & `image_validator.py`) [P5.5]
- **Scheme Check & SSRF Defense (`image_validator.py`)**: Requires HTTPS; resolves hostname and blocks loopback, private IPv4/IPv6 ranges (`127.0.0.0/8`, `10.0.0.0/8`, `172.16.0.0/12`, `192.168.0.0/16`, `169.254.0.0/16`, `::1`), and link-local addresses.
- **Byte-Level Validation (`images/validator.py`)**:
  - Enforces max byte size (8MB) and max dimensions (20 Megapixels).
  - Inspects file headers via Pillow for approved formats (`JPEG`, `PNG`, `WEBP`).
  - Catches `Image.DecompressionBombWarning` and decompression bomb errors to defend against malicious image payloads.
- **Safe Fetcher (`images/fetcher.py`)**: `SafeImageFetcher` streams responses with length limits, blocks SSRF hosts, and validates payload bytes before storage.
- **Independent Rights & Capability Split**:
  - *Listing Discovery*: Valid product schema and cleared source status.
  - *Image Display*: Source display rights + approved image rights (`owned`, `licensed`, `partner_authorized`).
  - *Virtual Try-On*: Source tryon rights + `image_policy="mirror"` + item tryon permission.

### 5. Multi-Factor Catalog Quality & Feed Eligibility (`eligibility.py`) [P5.6]
- **`CatalogEligibility` Evaluator**:
  - `is_discoverable`: Source cleared + product valid + title/category/brand present.
  - `is_purchasable`: Discoverable + offer `in_stock = True` + `price_minor > 0`.
  - `display_eligible`: Discoverable + source display permitted + image rights valid.
  - `tryon_eligible`: Display eligible + source tryon permitted + item tryon permitted.

### 6. Scheduled Sync, Exponential Retries & Reconciliation (`acquisition/` & `scripts/`) [P5.7]
- **Bounded Retries with Jitter (`acquisition/retry.py`)**: `retry_transient` wraps transient network errors with exponential backoff and randomized jitter to prevent thundering herds.
- **`CatalogSyncService` (`sync_service.py`)**: Orchestrates scheduled batch acquisition across all registered adapters with failure isolation (one source failing does not block other sources).
- **Stale Offer Reconciliation (`reconcile_stale_offers`)**: Automatically detects offers unrefreshed past a configured threshold (default 48h) and marks them `in_stock = False`, reconciling `CanonicalGarment.in_stock` accordingly.
- **CLI Sync Tool (`scripts/catalog/sync_sources.py`)**: Command-line interface supporting `--source <slug>`, `--all`, `--reconcile-stale`, `--dry-run`, and `--apply`.

### 7. Enrichment Pipeline Contract & Embedding Validation (`enrichment/jobs.py`) [P5.8]
- **`GarmentEnrichmentJob`**: Tracks enrichment lifecycle (`PENDING`, `RUNNING`, `COMPLETED`, `FAILED`).
- **`validate_embedding` Contract**:
  - Rejects zero-valued vectors (`norm == 0`).
  - Rejects non-finite values (`NaN`, `Inf`).
  - Enforces expected dimensionality (e.g. 512-d).
  - Explicitly rejects constant placeholder vectors (e.g., `[0.05] * 512`) with standard deviation checks.

### 8. Feed Candidate Integration (`backend/fashx/catalog/application/`) [P5.9]
- `list_feed_candidates` enforces source clearance, non-suspended merchant status, and valid canonical garment associations so that unapproved or corrupted listings cannot enter feed recommendations.

## Verification Results

| Check / Test Suite | Command | Result |
|---|---|---|
| Docs Lint | `python scripts/docs_lint.py` | `docs lint ok` |
| Python Ruff Linter | `ruff check .` | `All checks passed!` |
| Python Mypy Type Checker | `mypy .` | `Success: no issues found in 1022 source files` |
| Full Catalog Test Suite (17 files) | `python -m pytest tests/unit/test_*catalog* tests/unit/test_*acquisition* tests/unit/test_image* tests/unit/test_source* tests/unit/test_sync* tests/unit/test_enrichment* tests/integration/test_catalog* -v` | 66 passed in 13.89s |
| Sync Sources CLI Dry-Run (All Adapters) | `python scripts/catalog/sync_sources.py --all --dry-run --db-url sqlite+aiosqlite:///:memory:` | 4 sources synced (Amazon, Flipkart, Myntra, Manual-Demo): 14 inserted, 0 rejected |
| Stale Reconciliation CLI (SQLite) | `python scripts/catalog/sync_sources.py --reconcile-stale --max-age-hours 48 --apply --db-url sqlite+aiosqlite:///:memory:` | Executed cleanly, 0 stale offers detected |
| Mobile ESLint, TypeScript & Jest Suites | `cd mobile; npx eslint . --max-warnings 0; npx tsc --noEmit; npx jest --ci; cd ..` | 12 passed, 12 total (97 tests) |
| Android Expo Export | `cd mobile; npx expo export --platform android; cd ..` | 1591 modules bundled, exported to dist |

## P5 Checklist Execution Summary

- [x] **P5.0**: Audit catalog schema, migrations, API contracts, environment and test baseline.
- [x] **P5.1**: Catalog source registry and approval lifecycle; fail-closed validation for unregistered/unapproved sources.
- [x] **P5.2**: Source adapter contract (`CatalogSourceAdapter`), DTOs (`SourceProduct`, `AcquisitionBatch`), and registry.
- [x] **P5.3**: Product normalization & validation (taxonomies, integer paise, sizes, URL sanitizer).
- [x] **P5.4**: Idempotent product, canonical garment, and offer ingestion with change tracking and `IngestRun` auditing.
- [x] **P5.5**: Image acquisition, provenance, byte-level Pillow validation (decompression bombs, size limits), and SSRF defense.
- [x] **P5.6**: Catalog quality gate hardening and multi-factor item eligibility (`CatalogEligibility`).
- [x] **P5.7**: Incremental sync, bounded retries with jitter (`retry_transient`), and stale offer reconciliation (`reconcile_stale_offers`).
- [x] **P5.8**: Enrichment pipeline contract and strict embedding validation rejecting constant placeholder vectors.
- [x] **P5.9**: Feed candidate integration enforcing source clearance in `list_feed_candidates`.
- [x] **P5.10**: Integration tests, security checks, release gate, and comprehensive documentation.

## Known Blockers & Limitations (Rule 14)
- **Hosted PostgreSQL**: Backend tests were executed against SQLite in-memory; live PostgreSQL was unreachable locally (`[WinError 1225] The remote computer refused the network connection`) and remains unverified locally until CI run.
- **Live Commercial Store APIs**: Adapters for Amazon, Myntra, and Flipkart implement the full protocol with rate limiting and circuit breakers, tested against local authorized feeds; production API keys/credentials are not configured locally.
- **Physical Mobile Hardware**: Mobile validation completed via Jest tests, TypeScript type checking, and Expo Android static bundling; physical device test remains unverified.
