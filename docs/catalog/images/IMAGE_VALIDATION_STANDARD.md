# Image Validation Standard

## 1. Multi-Layer Validation Sequence

Every acquired image asset undergoes multi-tier validation:
1. **HTTP Content-Type**: Prohibits `text/html`, `application/pdf`, `image/svg+xml`.
2. **File Signatures (Magic Bytes)**:
   - JPEG: `\xff\xd8\xff`
   - PNG: `\x89PNG\r\n\x1a\n`
   - WebP: `RIFF....WEBP`
3. **Pillow Decoder Safety**: Format verified via Pillow parser; animated GIF and animated WebP rejected.
4. **Dimension Limits**:
   - Minimum: 400 × 400 px.
   - Maximum: 4096 × 4096 px.
   - Maximum Pixels: 20,000,000 px.
5. **Decompression Bomb Defense**: Catches `Image.DecompressionBombWarning` as rejection error.
6. **Orientation Normalization**: `ImageOps.exif_transpose` applies EXIF orientation before resizing.
7. **Metadata Hygiene**: Strips EXIF GPS coordinates, camera serial numbers, and device fingerprints from all derivatives.
