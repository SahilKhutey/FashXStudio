# RC07 — Enrichment Pipeline Correction

## 1. Objective
Refactor `HeuristicGarmentEnricher` to ensure deterministic attribute extraction while eliminating dead code, removing unused mock embedder instances, and enforcing that attribute extraction does not fabricate semantic vector embeddings.

## 2. Changes Applied
- **Module**: `backend/fashx/catalog/enrichment/enricher.py`
- **Removed**:
  - `from fashx.catalog.embeddings.fake import FakeEmbedder`
  - `self.embedder = FakeEmbedder()`
- **Enriched Attributes**:
  - `collar`: button_down, mandarin, spread, crew_neck, v_neck, polo_collar, notch_lapel
  - `sleeve_length`: long, short, sleeveless, three_quarter
  - `pattern`: striped, checkered, floral, printed, solid
  - `dominant_color`: mapped from color taxonomy, with image center-crop sampling fallback
  - `material`: 100% cotton, linen, denim, wool, silk, polyester
  - `formality`: formal, casual
  - `silhouette`: slim, regular
- **Confidence Calibration**:
  Each extracted field includes calibrated confidence floats in `[0.0, 1.0]`.
- **Architectural Boundary**:
  `EnrichmentResult.embedding` is explicitly returned as `None`. Vector embeddings must be generated only through authorized multimodal embedding providers.

## 3. Verification
Unit test `tests/unit/test_rc07_enrichment.py` confirms:
- Extraction of all 7 attributes from title and description.
- Image dominant color extraction fallback.
- Confidences bounded in `[0.0, 1.0]`.
- Explicit `embedding is None`.
- Graceful handling of empty or sparse inputs.
