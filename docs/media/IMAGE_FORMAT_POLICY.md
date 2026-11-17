# Image Format Policy

## 1. Supported Input Formats
To ensure maximum client compatibility, safe parsing, and high rendering quality, FashXStudio permits three image formats for personal photo ingestion:

| Format Name | Approved MIME Type | Container Extensions | Magic Bytes (Hex) |
|---|---|---|---|
| **JPEG** | `image/jpeg` | `.jpg`, `.jpeg` | `FF D8 FF` |
| **PNG** | `image/png` | `.png` | `89 50 4E 47 0D 0A 1A 0A` |
| **WebP** | `image/webp` | `.webp` | `52 49 46 46 ... 57 45 42 50` |

---

## 2. Strictly Prohibited Formats

| Format | Rejection Code | Security / Architecture Rationale |
|---|---|---|
| **GIF** | `unsupported_image_format` | Animation risks, excessive compression artifacts, low color depth |
| **SVG** | `unsupported_image_format` | XML/script injection risks (XSS, SSRF, XML entity expansion) |
| **BMP / TIFF** | `unsupported_image_format` | Uncompressed formats susceptible to memory inflation attacks |
| **HEIC / HEIF** | `unsupported_image_format` | Inconsistent cross-platform decoding libraries and licensing constraints |
| **Animated WebP** | `animated_image_unsupported` | Multi-frame imagery not applicable for single-pose fitting |

---

## 3. Container Verification Strategy
FashXStudio does **not** rely on client-supplied file extensions or declared `Content-Type` headers to verify file safety:
1. **Magic Bytes Inspection**: The first 12 bytes of raw input data are evaluated against known container signatures.
2. **Declared MIME Consistency**: The declared `Content-Type` header must match the magic bytes detected. Mismatches trigger `422 image_content_type_mismatch`.
3. **Strict Bounded Decode**: The image is decoded using Pillow with `ImageFile.LOAD_TRUNCATED_IMAGES = False` and `Image.MAX_IMAGE_PIXELS = 20_000_000`. Truncated, malformed, or bomb images trigger immediate rejection.

---

## 4. Mandatory Normalization
Once validated, the backend normalizes all images before storing them into final private storage:
- **Metadata Scrubbing**: All EXIF tags, GPS coordinate records, timestamp metadata, device model IDs, and embedded thumbnail images are completely removed.
- **Orientation Normalization**: EXIF orientation tags (e.g., orientation 6 or 8) are applied directly to the pixel raster via `ImageOps.exif_transpose`, rotating and flipping the pixels to upright orientation before EXIF is discarded.
- **Color Space Normalization**: CMYK or palette-based images are converted safely to standard sRGB. Alpha channels are preserved for transparent PNG/WebP assets (`RGBA`).
- **Standardized WebP Encoding**: All validated assets are re-encoded as optimized WebP raster files (`quality=90`, `method=6`). This ensures uniform byte structure, prevents polyglot exploits, reduces storage footprints by 30-40%, and eliminates any chance of malicious payload execution.
