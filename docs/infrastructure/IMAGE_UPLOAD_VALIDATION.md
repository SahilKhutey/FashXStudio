# FashXStudio — Image Upload Validation & Normalization Standard (Phase 03.4)

## 1. Security Invariants
Client-supplied headers and file extensions cannot be trusted. All uploaded media must be strictly verified on the backend before being promoted from `temporary/` to permanent private storage.

---

## 2. Limits Matrix

| Category | Permitted Formats | Max File Size | Max Dimensions | Max Decoded Pixels |
| :--- | :--- | :--- | :--- | :--- |
| **Shopper Photo** | JPEG, PNG, WebP | 10 MB | 4096 × 4096 | 20,000,000 |
| **Product Image** | JPEG, PNG, WebP | 15 MB | 4096 × 4096 | 20,000,000 |
| **VTO Result** | WebP, JPEG | 15 MB | 4096 × 4096 | 20,000,000 |

---

## 3. Strict Prohibitions
The following formats are rejected at the parser layer:
- **SVG / XML**: Potential Cross-Site Scripting (XSS) vectors.
- **HTML / Scripts**: Malicious executable payloads.
- **HEIC / AVIF**: Unverified native decoding in current MVP (deferred to future release).
- **Decompression Bombs**: Images exceeding 20 megapixels that consume excessive memory when uncompressed.

---

## 4. Processing Pipeline (`image_validation.py`)
1. **Header Verification**: Inspects magic bytes via `PIL.Image.open().verify()`.
2. **Format Match Verification**: Rejects payloads where detected format does not match declared MIME type (e.g. PNG binary masquerading as JPEG).
3. **Dimension & Pixel Checks**: Enforces `width <= 4096`, `height <= 4096`, and `width * height <= 20,000,000`.
4. **EXIF Stripping & Auto-Orientation**: Runs `ImageOps.exif_transpose()` to preserve correct camera orientation, then discards all EXIF metadata (camera model, GPS coordinates, timestamps).
5. **Color Mode Normalization**: Converts non-RGBA images to RGB.
6. **WebP Re-encoding**: Re-encodes the image into WebP format (`quality = 90`, `method = 6`).
