# Phase 08.4 Scoring Policy

## Initial Weights (`personalized-v1`)
- Category relevance: `0.20`
- Style preference: `0.15`
- Colour preference: `0.10`
- Price preference: `0.10`
- Availability: `0.10`
- Size availability: `0.10`
- Visual similarity: `0.10`
- Explicit feedback: `0.10`
- Product/merchant quality: `0.05`

## Baseline Weights (`baseline-v1`)
- Category relevance: `0.45`
- Availability: `0.25`
- Product/merchant quality: `0.20`
- Price preference: `0.10`

Optional features (`visual_similarity`, `size_availability_score`) are omitted from the denominator when `None` so missing context never penalizes eligible products.
