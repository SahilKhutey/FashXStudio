# Phase 08.4 Architecture & Integration

## Pipeline
1. **Retrieval**: Candidate products and active merchant offers are retrieved.
2. **Eligibility & Safety Gate (`eligibility.py`)**: Enforces active product/offer status, zero takedowns/delistings/discontinuations, active Phase 05 display/redirect/image permissions, confirmed `IN_STOCK` availability within freshness bounds, valid price/currency, and selected-size availability when required.
3. **Feature Generation (`features.py`)**: Builds normalized `[0.0, 1.0]` features with provenance (`taxonomy`, `shopper_profile_rev`, `offer`, `variants`, `embedding`, `feedback_events`, `merchant`).
4. **Deterministic Scoring & Tie-Breaking (`scorer.py`, `service.py`)**: Computes $100 \times \frac{\sum_{i \in A} w_i f_i}{\sum_{i \in A} w_i}$ over applicable (non-`None`) features, then sorts by `(-score, -category_score, -availability_freshness, -quality_score, product_id)`.
5. **Explanations (`explanations.py`)**: Emits shopper-facing reason codes only when backed by positive feature contributions. Never claims physical fit guarantees.
