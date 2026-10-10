# Phase 7: Ranker Weight Tuning & Coordinate Ascent

**Date**: 2026-10-10  
**Train Personas (9)**: p01, p02, p03, p05, p06, p07, p09, p10, p11  
**Holdout Personas (3)**: p04 (Professional), p08 (Wedding/Royal), p12 (Relaxed Fit)  
**ADR-0006 Promotion Threshold**: Holdout nDCG@10 >= +0.020  

## Optimization Scorecard

| Metric | Baseline (v1) | Tuned Candidate | Delta | Promotion Status |
|---|---|---|---|---|
| **Train nDCG@10 (9 Personas)** | 0.8602 | 0.8602 | +0.0000 | - |
| **Holdout nDCG@10 (3 Personas)** | 0.9077 | 0.9077 | **+0.0000** | **REJECT V2 (KEEP V1)** |

## Tuned Weights Comparison

| Feature | v1 Baseline Weight | Tuned Weight | Rationale |
|---|---|---|---|
| `taste` | 1.00 | 1.00 | Coordinate ascent delta: +0.00 |
| `style` | 0.50 | 0.50 | Coordinate ascent delta: +0.00 |
| `occasion` | 0.40 | 0.40 | Coordinate ascent delta: +0.00 |
| `formality` | 0.30 | 0.30 | Coordinate ascent delta: +0.00 |
| `color` | 0.30 | 0.30 | Coordinate ascent delta: +0.00 |
| `skin_harmony` | 0.10 | 0.10 | Coordinate ascent delta: +0.00 |
| `size_fit` | 0.40 | 0.40 | Coordinate ascent delta: +0.00 |
| `price` | 0.30 | 0.30 | Coordinate ascent delta: +0.00 |
| `freshness` | 0.15 | 0.15 | Coordinate ascent delta: +0.00 |
| `popularity` | 0.10 | 0.10 | Coordinate ascent delta: +0.00 |
| `tryon` | 0.00 | 0.00 | Coordinate ascent delta: +0.00 |

## Decision & Gate Action

- **Decision**: Holdout nDCG@10 delta was **+0.0000** (< +0.020 required by ADR-0006).
- In accordance with ADR-0006 non-negotiable decision rule: **v1 remains the active ranker**.
- Candidate v2 was rejected to prevent overfitting to training judgments.
