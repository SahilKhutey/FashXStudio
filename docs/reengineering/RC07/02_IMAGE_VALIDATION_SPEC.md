# RC07 — Image Validation Specification

## 1. Objective
Ensure that external and ingested garment images are strictly validated at the byte and dimensional level before entering storage, enrichment, or embedding generation pipelines.

## 2. Validation Bounds
- **Module**: `backend/fashx/catalog/images/validator.py`
- **Minimum Dimension**: 128 x 128 pixels (`MIN_IMAGE_DIMENSION = 128`).
- **Maximum Resolution**: 20,000,000 pixels (`MAX_IMAGE_PIXELS = 20_000_000`).
- **Maximum Byte Size**: 8 MB (`MAX_IMAGE_BYTES = 8 * 1024 * 1024`).
- **Allowed MIME Formats**: `{"JPEG", "PNG", "WEBP"}`.
- **Security Protections**:
  - `Image.DecompressionBombWarning` treated as hard error.
  - SSRF validation via `SafeImageValidator.is_ssrf_safe_host`: blocks private IP literals, loopbacks, link-local, multicast, and internal domains (`.local`, `.internal`).
  - Source clearance verification: requires `source_status == "cleared"` and `source_rights_display is True`.
  - Try-on eligibility verification: requires `source_rights_tryon is True` and `source_image_policy == "mirror"`.

## 3. Verification
Unit test `tests/unit/test_rc07_image_validation.py` verifies:
- Rejection of empty byte payloads.
- Rejection of malformed/corrupted byte streams.
- Rejection of undersized images (<128x128).
- Acceptance of valid JPEG, PNG, WEBP images.
- Full rights and license evaluation logic.
