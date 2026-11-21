# Visual Similarity Search Specification

## 1. Overview
Visual search allows shoppers to upload a reference photograph or select an existing catalog image to discover visually similar products (matching silhouettes, colors, patterns, and styling).

---

## 2. Privacy & Security Workflow (Rule I06)
1. **Reference Asset Validation**: Shopper uploads are validated for file format (JPEG, PNG, WebP) and dimensions ($100 \times 100$ to $4096 \times 4096$ px).
2. **Ephemeral Processing**: Reference photos are processed transiently; they are **never stored indefinitely** and **never used for model training**.
3. **No Biometric Extraction**: Facial and biometric feature recognition is strictly prohibited. Only garment region pixels are embedded.
4. **Self-Hosted Inference**: Vectors are generated on self-hosted inference workers using the Phase 06.3 approved OpenCLIP ViT-B/32 vision encoder.

---

## 3. Query Execution & Catalog Visibility
- The query image is preprocessed through `fashx.catalog.embeddings.preprocessing` (EXIF transpose, aspect-ratio preserved scaling with neutral padding).
- The 512-dim L2-normalized vector is searched against `product_image_embeddings` using HNSW cosine distance (`<=>`).
- Takedown and delisted products are strictly filtered out before returning results.
