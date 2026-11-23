# Image Test Strategy

## 1. Test Architecture

The image pipeline test suite spans 45 test specifications (IMG-001 through IMG-045) organized across 4 dedicated test modules in `tests/unit/catalog/`:

1. **`test_product_image_validation.py`**:
   - Focus: Magic bytes, MIME checks, format safety, decompression bomb protection, dimension limits, EXIF transposition, metadata stripping, deterministic SHA-256 and perceptual dHash consistency.
   - Covers: IMG-010 to IMG-024, IMG-027.
2. **`test_product_image_pipeline.py`**:
   - Focus: Preflight permission evaluation, fail-closed behavior, display derivative creation, VTO derivative rights checks, database failure compensation cleanup, 404 handling, duplicate job delivery idempotency, permission service outage handling.
   - Covers: IMG-001 to IMG-009, IMG-028 to IMG-033, IMG-038 to IMG-040, IMG-044, IMG-045.
3. **`test_product_image_storage.py`**:
   - Focus: Exact original deduplication, shared stock image cross-product isolation, signed URL generation and expiry.
   - Covers: IMG-025, IMG-026, IMG-041, IMG-043.
4. **`test_product_image_takedown.py`**:
   - Focus: Immediate asset suspension, cascade deletion across originals and derivatives, physical storage verification, partial failure handling with retry tracking.
   - Covers: IMG-034 to IMG-037, IMG-042.

---

## 2. Invariant: No External Network or Cloud Calls in Tests

All tests execute with local fixtures, memory images, and mock transports, guaranteeing zero dependencies on external internet access or live AWS credentials during CI test runs.
