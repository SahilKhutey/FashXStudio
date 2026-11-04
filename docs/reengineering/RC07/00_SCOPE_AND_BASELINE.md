# RC07 — Scope and Baseline

## 1. Baseline Position
- **Repository**: `SahilKhutey/FashXStudio`
- **Branch**: `recovery/rc07-catalog-personalization`
- **Baseline Commit**: `db2609e4a8ae3c6fe687c03d81e54ddad86d1f59` (origin/main)
- **Target Remote**: `origin/recovery/rc07-catalog-personalization`

## 2. In-Scope Components
1. **Catalog Enrichment**:
   - Extraction of collar, sleeve length, pattern, dominant color, material, formality, silhouette from metadata and image bytes.
   - Elimination of unused `FakeEmbedder` imports from heuristic enricher.
   - Purity guarantee: `embedding=None` returned from enricher.
2. **Image Validation**:
   - Minimum dimensions (128x128), max dimensions (20 Megapixels), byte limits (8MB).
   - Format validation (`JPEG`, `PNG`, `WEBP`).
   - Source clearance and rights validation.
3. **Multimodal Embeddings**:
   - Provider protocol `ImageTextEmbedder` with explicit `model_version: str`.
   - Real provider revision pinned to `Marqo/marqo-fashionCLIP:2026.1`.
   - Deterministic test provider pinned to `mock-fake-512:mock-v1` with production prohibition guard.
   - `EmbeddingService` for input/output verification.
4. **Behavioral Personalization & Taste Vector**:
   - Signal weights: `like` (1.0), `save` (1.2), `try_on` (1.5), `hide` (-1.0), `not_interested` (-1.0).
   - 14-day half-life exponential time decay: `0.5 ** (delta_days / 14.0)`.
   - Cross-model compatibility filtering (discard incompatible model vectors).
   - Cold-start fallback to deterministic preference compatibility without fake vectors.
5. **Feed Scoring & Constraints**:
   - 8-feature `RankingWeights(style=0.18, occasion=0.10, color=0.10, size=0.18, budget=0.14, freshness=0.10, semantic=0.15, tryon=0.05)`.
   - Dynamic reweighting for missing features.
   - Hard candidate gating: active, in-stock, cleared sources, display rights, budget limit, size availability, excluded garment IDs.
   - MMR diversification with brand and subcategory caps.
   - Truthful grounded reason chips and stylist explanations.

## 3. Out-of-Scope Boundaries
- **Merchant Payment Card Processing**: No checkout completion or direct card transactions. External retailer redirection remains authoritative.
- **Speculative Fit Guarantees**: No hallucinated or unmeasured body measurement claims.
