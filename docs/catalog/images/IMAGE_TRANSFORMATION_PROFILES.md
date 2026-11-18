# Image Transformation Profiles

## 1. Specifications for Display Derivatives

Display derivatives optimize consumer browsing speeds, bandwidth efficiency, and visual appeal while preserving fabric textures and true apparel colors:

| Profile | Target Format | Max Bounds | Quality | Scaling Strategy | Neutral Background |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **`DISPLAY_THUMBNAIL`** | WebP | 384 × 384 px | 80 | Preserves aspect ratio, Lanczos filter | Pastes on pure white `#FFFFFF` |
| **`DISPLAY_CARD`** | WebP | 768 × 768 px | 82 | Preserves aspect ratio, Lanczos filter | Pastes on pure white `#FFFFFF` |
| **`DISPLAY_DETAIL`** | WebP | 1200 × 1200 px | 85 | Preserves aspect ratio, Lanczos filter | Pastes on pure white `#FFFFFF` |

---

## 2. Invariant: Immutability and Versioning

- Derivatives are never overwritten in-place.
- A new transformation profile or algorithm change increments `transformation_version` (e.g. `v1` $\rightarrow$ `v2`) and inserts an independent record in `catalog_image_transformations`.
