# Image Size and Dimension Limits

## 1. Boundary Limits Overview

| Boundary Dimension | Minimum Limit | Maximum Limit | Rejection Code |
|---|---|---|---|
| **Raw File Size** | 10 KB (`10,240` bytes) | 10 MB (`10,485,760` bytes) | `image_size_below_minimum` / `image_size_exceeded` |
| **Canvas Dimensions** | 1 px | 4096 px (width or height) | `image_dimensions_exceeded` |
| **Total Pixel Count** | 1 pixel | 20,000,000 pixels (20 MP) | `image_dimensions_exceeded` |
| **Aspect Ratio Range** | 1:4 (0.25) | 4:1 (4.00) | Validated during profile processing |

---

## 2. Minimum Size Limit Rationale (10 KB)
- A genuine, camera-captured portrait or full-body photograph containing sufficient detail for virtual try-on or profile identification requires at least 15-20 KB of compressed data.
- Files under 10 KB typically represent corrupted placeholder files, 1x1 tracking pixels, empty files, or micro-payload injection attempts.

---

## 3. Maximum Size Limit Rationale (10 MB)
- High-end mobile cameras capture 12 MP to 48 MP photos that compress down to 2 MB to 8 MB under standard JPEG or HEIC/JPEG compression.
- 10 MB accommodates full-resolution mobile camera captures without requiring aggressive local downscaling.
- Setting a hard ceiling at 10 MB prevents denial-of-service (DoS) attacks targeting network bandwidth and memory buffers.

---

## 4. Canvas Dimension & Pixel Limits (4096px / 20 Megapixels)
- **Maximum Dimension (4096 px)**: 4K resolution (3840×2160) easily fits within the 4096 px boundary. Images exceeding 4096 px require significant raster memory without providing discernible try-on quality improvements.
- **Decompression Bomb Protection (20 MP)**: Malicious image files ("zip bombs" or "pixel floods") can have tiny compressed file sizes (e.g., 50 KB) that expand to gigabytes of uncompressed RGBA pixel buffers in memory ($W \times H \times 4\text{ bytes}$).
- By hard-capping total decoded pixels at 20,000,000, uncompressed memory consumption per validation worker is strictly bounded to $\approx 80\text{ MB}$, preventing memory exhaustion across background pods and server containers.
